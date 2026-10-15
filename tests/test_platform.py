import json
import shutil
import unittest
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path

import numpy as np

from medmlops.api import create_app
from medmlops.cli import main
from medmlops.data import FEATURES, generate, validate
from medmlops.model import drift, predict
from medmlops.store import Store
from medmlops.train import quality_gate, train

TOKEN = "test-only-token-123456789"
RECORD = dict(zip(FEATURES, [68, 105, 110, 94, 38], strict=True))
TEST_ROOT = Path(__file__).resolve().parents[1] / "runtime" / "tests"
TEST_ROOT.mkdir(parents=True, exist_ok=True)


@contextmanager
def test_directory():
    # Default inherited permissions work in managed Windows workspaces.
    path = TEST_ROOT / uuid.uuid4().hex
    path.mkdir()
    try:
        yield str(path)
    finally:
        resolved = path.resolve()
        if resolved.parent != TEST_ROOT.resolve():
            raise ValueError("Unsafe test cleanup path")
        shutil.rmtree(resolved)


test_directory.__test__ = False


class PlatformTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_context = test_directory()
        cls.temp_name = cls.temp_context.__enter__()
        cls.store = Store(cls.temp_name)
        cls.first = train(cls.store)
        cls.second = train(cls.store, seed=43)
        cls.store.promote(cls.first["version"])

    @classmethod
    def tearDownClass(cls):
        cls.temp_context.__exit__(None, None, None)

    def setUp(self):
        self.store.promote(self.first["version"])
        self.client = create_app(self.temp_name, TOKEN).test_client()
        self.auth = {"Authorization": "Bearer " + TOKEN}

    def test_determinism_and_disjoint_splits(self):
        repeated = train(self.store)
        self.assertEqual(self.first["version"], repeated["version"])
        x1, y1 = generate()
        x2, y2 = generate()
        np.testing.assert_array_equal(x1, x2)
        np.testing.assert_array_equal(y1, y2)
        from sklearn.model_selection import train_test_split
        a, h = train_test_split(np.arange(len(y1)), test_size=.4, random_state=42, stratify=y1)
        v, t = train_test_split(h, test_size=.5, random_state=42, stratify=y1[h])
        self.assertFalse(set(a) & set(v) or set(a) & set(t) or set(v) & set(t))
        self.assertEqual(len(set(a) | set(v) | set(t)), 4000)
        self.assertLess(self.first["report"]["train_serve_max_error"], 1e-12)

    def test_gate_rejects_bad_model(self):
        report = json.loads(json.dumps(self.first["report"]))
        report["test"]["sensitivity"] = .1
        checks, passed = quality_gate(report["test"], report["slices"])
        self.assertFalse(passed)
        self.assertFalse(checks["sensitivity_ge_0.75"])
        self.assertFalse(quality_gate(self.first["report"]["test"], {})[1])
        _, bundle = self.store.load()
        bundle["seed"] = -1
        report["passed"] = passed
        version = self.store.save(bundle, report)
        with self.assertRaises(ValueError):
            self.store.promote(version)
        self.assertEqual(self.store.load()[0], self.first["version"])

    def test_promotion_rollback_and_missing_version(self):
        self.assertTrue(self.second["report"]["passed"])
        self.store.promote(self.second["version"])
        self.assertEqual(self.store.load()[0], self.second["version"])
        self.store.promote(self.first["version"], rollback=True)
        self.assertEqual(self.store.load()[0], self.first["version"])
        with self.assertRaises(OSError):
            self.store.promote("0" * 64)
        with self.assertRaises(ValueError):
            self.store.load("../secrets")

    def test_corruption_blocks_readiness_and_inference(self):
        with test_directory() as root:
            local = Store(root)
            _, bundle = self.store.load()
            version = local.save(bundle, self.first["report"])
            local.promote(version)
            (Path(root) / "models" / f"{version}.json").write_text("{}")
            client = create_app(root, TOKEN).test_client()
            self.assertEqual(client.get("/health/ready").status_code, 503)
            self.assertEqual(client.post("/api/predict", json={"records": [RECORD]}, headers=self.auth).status_code, 503)

    def test_authentication_and_input_privacy(self):
        self.assertEqual(self.client.get("/api/status").status_code, 401)
        self.assertEqual(self.client.get("/api/status", headers={"Authorization": "Bearer é"}).status_code, 401)
        self.assertEqual(self.client.post("/api/predict", json={}, headers={"Authorization": "Bearer wrong"}).status_code, 401)
        payload = {"records": [{**RECORD, "patient_name": "PRIVATE_SENTINEL"}]}
        response = self.client.post("/api/predict", json=payload, headers=self.auth)
        self.assertEqual(response.status_code, 422)
        self.assertNotIn("PRIVATE_SENTINEL", response.get_data(as_text=True))
        self.assertNotIn("PRIVATE_SENTINEL", json.dumps(self.store.status()))

    def test_feature_contract_adversarial(self):
        for invalid in ([], [None], [dict(RECORD, age=True)], [dict(RECORD, age="68")],
                        [dict(RECORD, age=float("nan"))], [dict(RECORD, age=float("inf"))],
                        [dict(RECORD, age=101)], [{"age": 20}], [RECORD] * 1001):
            with self.subTest(invalid=str(invalid)[:50]), self.assertRaises(ValueError):
                validate(invalid)
        self.assertEqual(validate([RECORD]).shape, (1, 5))

    def test_prediction_parity_audit_and_health(self):
        self.assertEqual(self.client.get("/health/live").status_code, 200)
        self.assertEqual(self.client.get("/health/ready").status_code, 200)
        r = self.client.post("/api/predict", json={"records": [RECORD]}, headers=self.auth)
        self.assertEqual(r.status_code, 200)
        _, bundle = self.store.load()
        expected = predict(bundle, validate([RECORD]))[0]
        self.assertAlmostEqual(r.json["predictions"][0]["probability"], expected, places=12)
        event = self.store.status()["audit"][0]
        self.assertEqual(event["event"], "prediction")
        self.assertEqual(set(event["detail"]), {"count", "latency_ms"})
        self.assertEqual(r.headers["Cache-Control"], "no-store")

    def test_monitor_detects_shift_without_false_alert_on_reference(self):
        _, bundle = self.store.load()
        stable, _ = generate(1000, 99)
        shifted, _ = generate(1000, 99, shifted=True)
        self.assertFalse(drift(bundle, stable)["alert"])
        self.assertTrue(drift(bundle, shifted)["alert"])
        records = [dict(zip(FEATURES, row.tolist(), strict=True)) for row in shifted]
        r = self.client.post("/api/monitor", json={"records": records}, headers=self.auth)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.json["alert"])
        self.assertEqual(self.client.post("/api/monitor", json={"records": [RECORD]}, headers=self.auth).status_code, 422)

    def test_empty_registry_and_no_secret_defaults(self):
        with test_directory() as root:
            client = create_app(root, TOKEN).test_client()
            self.assertEqual(client.get("/health/ready").status_code, 503)
            self.assertEqual(client.post("/api/predict", json={"records": [RECORD]}, headers=self.auth).status_code, 503)
        with self.assertRaises(ValueError):
            create_app(self.temp_name, "short")

    def test_malformed_large_body_and_web_dashboard(self):
        self.assertEqual(self.client.post("/api/predict", data="{invalid", content_type="application/json", headers=self.auth).status_code, 400)
        self.assertEqual(self.client.post("/api/predict", data="x" * (1024 * 1024 + 1), content_type="application/json", headers=self.auth).status_code, 413)
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("MedMLOps", r.get_data(as_text=True))
        r.close()

    def test_concurrent_audit_and_registry(self):
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda i: self.store.audit("concurrency_test", self.first["version"], {"i": i}), range(20)))
        events = [r for r in self.store.status()["audit"] if r["event"] == "concurrency_test"]
        self.assertEqual(len(events), 20)

    def test_batch_command_and_overwrite_protection(self):
        with test_directory() as root:
            source, target = Path(root) / "input.json", Path(root) / "output.json"
            source.write_text(json.dumps([RECORD]))
            args = ["--root", self.temp_name, "batch", str(source), str(target)]
            self.assertEqual(main(args), 0)
            self.assertEqual(len(json.loads(target.read_text())["probabilities"]), 1)
            self.assertEqual(main(args), 1)


if __name__ == "__main__":
    unittest.main()
