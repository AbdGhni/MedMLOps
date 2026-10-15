import hashlib
import json
import shutil
import unittest
import uuid
from pathlib import Path

import numpy as np
from pydantic import ValidationError

from medmlops.candidate_validation import validate_structure, verify_candidate
from medmlops.data import canonical
from medmlops.datasets import Measurement, generate, load_snapshot, snapshot, validate
from medmlops.experiments import gate, prepare, run
from medmlops.monitor_windows import monitor
from medmlops.scoring import predict


class DataTests(unittest.TestCase):
    def test_synthetic_reproducibility_and_contract(self):
        first, second = generate(), generate()
        self.assertTrue(first.equals(second))
        self.assertTrue(validate(first)["passed"])
        record = first.drop(columns=["synthetic_id", "target"]).iloc[0].to_dict()
        record["sex_code"] = int(record["sex_code"])
        record["prior_event"] = int(record["prior_event"])
        self.assertEqual(len(Measurement(**record).model_dump()), 10)
        for update in ({"age": "68"}, {"age": True}, {"crp": float("nan")},
                       {"patient_name": "forbidden"}, {"sex_code": .5}, {"prior_event": True}):
            with self.subTest(update=update), self.assertRaises(ValidationError):
                Measurement(**{**record, **update})

    def test_quality_failures(self):
        for change in ("missing", "duplicate", "outlier", "labels", "extra", "nonbinary"):
            frame = generate()
            if change == "missing":
                frame.loc[0, "age"] = np.nan
            elif change == "duplicate":
                frame.loc[1, "synthetic_id"] = frame.loc[0, "synthetic_id"]
            elif change == "outlier":
                frame.loc[0, "creatinine"] = 10
            elif change == "labels":
                frame.target = 0
            elif change == "extra":
                frame["target_copy"] = frame.target
            else:
                frame["prior_event"] = frame.prior_event.astype(bool)
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate(frame)


class ExperimentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path("runtime/tests-v2") / uuid.uuid4().hex
        cls.root.mkdir(parents=True)
        cls.config = json.loads(Path("configs/params.json").read_text())
        cls.version = snapshot(cls.root / "raw")["version"]
        prepare(cls.root / "raw", cls.version, cls.root / "prepared", 42)
        cls.result = run(cls.root / "prepared", cls.root / "artifacts", cls.config)
        # Actual fitted artifacts are copied into the normal pipeline layout.
        cls.review_root = cls.root / "review"
        cls.review_root.mkdir()
        shutil.copytree(cls.root / "prepared", cls.review_root / "prepared")
        shutil.copytree(cls.root / "artifacts", cls.review_root / "candidates")
        (cls.review_root / "comparison.json").write_bytes(canonical(cls.result))

    @classmethod
    def tearDownClass(cls):
        resolved = cls.root.resolve()
        if resolved.parent != Path("runtime/tests-v2").resolve():
            raise ValueError("Unsafe test cleanup")
        shutil.rmtree(resolved)

    def test_version_and_integrity(self):
        repeated = snapshot(self.root / "raw")
        self.assertEqual(repeated["version"], self.version)
        self.assertNotEqual(snapshot(self.root / "raw", seed=43)["version"], self.version)
        folder = self.root / "raw" / self.version
        original = (folder / "cohort.csv").read_bytes()
        try:
            (folder / "cohort.csv").write_bytes(original + b"corrupt")
            with self.assertRaises(ValueError):
                load_snapshot(self.root / "raw", self.version)
        finally:
            (folder / "cohort.csv").write_bytes(original)
        prepared = self.root / "prepared/splits.npz"
        original_prepared = prepared.read_bytes()
        try:
            prepared.write_bytes(original_prepared + b"modified")
            with self.assertRaises(ValueError):
                run(self.root / "prepared", self.root / "artifacts", self.config)
        finally:
            prepared.write_bytes(original_prepared)

    def test_disjoint_subject_partitions(self):
        with np.load(self.root / "prepared/splits.npz", allow_pickle=False) as arrays:
            sets = [set(arrays[f"ids_{s}"].tolist()) for s in ("train", "validation", "test")]
            self.assertEqual([len(s) for s in sets], [2400, 800, 800])
            self.assertFalse(sets[0] & sets[1] or sets[0] & sets[2] or sets[1] & sets[2])
            self.assertEqual(len(set.union(*sets)), 4000)

    def test_two_models_cv_calibration_metrics_and_parity(self):
        self.assertEqual(set(self.result["models"]), {"logistic", "forest"})
        for report in self.result["models"].values():
            self.assertEqual(len(report["cv"]["folds"]), 5)
            self.assertLess(report["parity_max_error"], 1e-12)
            self.assertEqual(report["dataset_version"], self.version)
            self.assertEqual(len(report["git_commit"]), 40)
            self.assertIn("pydantic", report["environment"])
            self.assertTrue(set(report["test"]) >= {"auc", "pr_auc", "sensitivity", "specificity", "f1", "brier", "calibration", "confusion"})
            bundle = json.loads((self.root / "artifacts" / report["model_sha256"] / "model.json").read_text())
            self.assertEqual(hashlib.sha256(canonical(bundle)).hexdigest(), report["model_sha256"])
            with np.load(self.root / "prepared/splits.npz", allow_pickle=False) as arrays:
                p = predict(bundle, arrays["x_test"])
                self.assertTrue(np.all((p >= 0) & (p <= 1)))

    def test_selection_uses_validation_and_gate_rejects_regression(self):
        expected = max(self.result["models"], key=lambda k: self.result["models"][k]["validation"]["auc"])
        self.assertEqual(self.result["selected"], expected)
        decision = gate(self.result, self.config)
        self.assertTrue(decision["selected_passed"])
        degraded = json.loads(json.dumps(self.result))
        degraded["models"][expected]["test"]["auc"] = .5
        self.assertFalse(gate(degraded, self.config)["selected_passed"])
        self.assertFalse(decision["promotion_performed"])
        checked = gate(self.result, self.config, self.root / "artifacts")
        self.assertTrue(checked["selected_passed"])
        model_path = self.root / "artifacts" / self.result["models"][expected]["model_sha256"] / "model.json"
        original = model_path.read_bytes()
        try:
            model_path.write_text("{}")
            self.assertFalse(gate(self.result, self.config, self.root / "artifacts")["selected_passed"])
        finally:
            model_path.write_bytes(original)

    def test_monitoring_types_labels_and_small_windows(self):
        report = self.result["models"][self.result["selected"]]
        bundle = json.loads((self.root / "artifacts" / report["model_sha256"] / "model.json").read_text())
        reference = generate(1000, 97)
        current = generate(1000, 99)
        stable = monitor(bundle, reference, current, self.config["monitoring"])
        self.assertFalse(stable["alerts"])
        self.assertEqual(stable["performance"]["status"], "unavailable")
        shifted = generate(1000, 99, shifted=True)
        drifted = monitor(bundle, reference, shifted, self.config["monitoring"])
        self.assertIn("data_drift", {a["type"] for a in drifted["alerts"]})
        self.assertTrue(drifted["prediction_drift"]["alert"])
        self.assertEqual(monitor(bundle, reference, current.head(99), self.config["monitoring"])["status"], "inconclusive")
        measured = monitor(bundle, reference, current, self.config["monitoring"],
                           labels=current.target.to_numpy(), reference_metrics=report["test"])
        self.assertEqual(measured["performance"]["status"], "measured")
        degraded = monitor(bundle, reference, current, self.config["monitoring"],
                           labels=1 - current.target.to_numpy(), reference_metrics=report["test"])
        self.assertIn("performance_degradation", {a["type"] for a in degraded["alerts"]})
        self.assertFalse(degraded["automatic_training"])
        self.assertFalse(degraded["automatic_promotion"])
        with self.assertRaises(ValueError):
            monitor(bundle, reference, current, self.config["monitoring"], labels=[1, 0])

    def test_candidate_metrics_recomputed_from_real_artifacts(self):
        for kind in ("logistic", "forest"):
            checked = verify_candidate(self.review_root, kind, "test-operator")
            self.assertTrue(checked["checks"]["metrics_recomputed_match"])
            self.assertTrue(checked["checks"]["confusion_recomputed_match"])
            self.assertFalse(checked["promotion_performed"])
            self.assertFalse(checked["approval_performed"])

    def test_candidate_rejects_tampered_metrics_and_missing_actor(self):
        path = self.review_root / "comparison.json"
        original = path.read_bytes()
        altered = json.loads(original)
        altered["models"]["logistic"]["test"]["auc"] = 1.0
        try:
            path.write_bytes(canonical(altered))
            checked = verify_candidate(self.review_root, "logistic", "test-operator")
            self.assertFalse(checked["checks"]["metrics_recomputed_match"])
            with self.assertRaises(ValueError):
                verify_candidate(self.review_root, "logistic", "")
            with self.assertRaises(ValueError):
                verify_candidate(self.review_root, "logistic", "operator\nforged-event")
        finally:
            path.write_bytes(original)

    def test_candidate_rejects_unsafe_numeric_artifacts(self):
        for kind in ("logistic", "forest"):
            report = self.result["models"][kind]
            bundle = json.loads((self.root / "artifacts" / report["model_sha256"] / "model.json").read_text())
            validate_structure(bundle)
            if kind == "logistic":
                bundle["scale"][0] = 0
            else:
                bundle["trees"][0]["left"][0] = 0
            with self.assertRaises(ValueError):
                validate_structure(bundle)


if __name__ == "__main__":
    unittest.main()
