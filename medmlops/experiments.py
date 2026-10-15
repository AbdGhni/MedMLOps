"""Offline v2 experiments. MLflow publication is a separate required integration."""
import hashlib
import importlib.metadata
import json
import platform
import subprocess
import uuid
from pathlib import Path

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import auc, f1_score, precision_recall_curve
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import canonical
from .datasets import FEATURES, load_snapshot
from .scoring import export_model, predict
from .train import metrics


def evaluate(y, probabilities, threshold):
    result = metrics(y, probabilities, threshold)
    precision, recall, _ = precision_recall_curve(y, probabilities)
    fraction, mean = calibration_curve(y, probabilities, n_bins=10)
    return {**result, "pr_auc": float(auc(recall, precision)),
            "f1": float(f1_score(y, probabilities >= threshold)),
            "calibration": {"observed": fraction.tolist(), "predicted": mean.tolist()}}


def prepare(raw_root, version, output, seed):
    frame, manifest = load_snapshot(raw_root, version)
    idx = np.arange(len(frame))
    train, rest = train_test_split(idx, test_size=.4, random_state=seed, stratify=frame.target)
    validation, test = train_test_split(rest, test_size=.5, random_state=seed, stratify=frame.target.iloc[rest])
    path = Path(output)
    path.mkdir(parents=True, exist_ok=True)
    arrays = {}
    for name, indices in (("train", train), ("validation", validation), ("test", test)):
        arrays[f"x_{name}"] = frame.iloc[indices][list(FEATURES)].to_numpy(dtype=float)
        arrays[f"y_{name}"] = frame.target.iloc[indices].to_numpy(dtype=int)
        arrays[f"ids_{name}"] = frame.synthetic_id.iloc[indices].to_numpy(dtype=str)
    np.savez_compressed(path / "splits.npz", **arrays)
    provenance = {**manifest, "split_seed": seed, "fractions": [.6, .2, .2],
                  "prepared_sha256": hashlib.sha256((path / "splits.npz").read_bytes()).hexdigest(),
                  "counts": {name: len(arrays[f"y_{name}"]) for name in ("train", "validation", "test")}}
    (path / "manifest.json").write_bytes(canonical(provenance))
    return provenance


def run(prepared, artifacts, config):
    prepared = Path(prepared)
    dataset = json.loads((prepared / "manifest.json").read_text())
    if hashlib.sha256((prepared / "splits.npz").read_bytes()).hexdigest() != dataset["prepared_sha256"]:
        raise ValueError("Prepared dataset integrity failed")
    with np.load(prepared / "splits.npz", allow_pickle=False) as saved:
        arrays = {name: saved[name] for name in saved.files}
    partitions = [set(arrays[f"ids_{name}"].tolist()) for name in ("train", "validation", "test")]
    if partitions[0] & partitions[1] or partitions[0] & partitions[2] or partitions[1] & partitions[2]:
        raise ValueError("Patient overlap across partitions")
    seed = config["training"]["seed"]
    candidates = {
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(random_state=seed, max_iter=1000)),
        "forest": RandomForestClassifier(n_estimators=config["training"]["forest_trees"],
                                          max_depth=config["training"]["forest_max_depth"],
                                          min_samples_leaf=10, random_state=seed, n_jobs=1),
    }
    commit = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True)
    if commit.returncode != 0:
        raise ValueError("A committed Git repository is required for experiment provenance")
    dirty = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, check=True)
    source_hash = hashlib.sha256(b"".join((Path(__file__).parent / name).read_bytes()
                                        for name in ("datasets.py", "scoring.py", "experiments.py", "train.py"))).hexdigest()
    environment = {name: importlib.metadata.version(name) for name in
                   ("numpy", "pandas", "scikit-learn", "pydantic", "scipy")}
    environment["python"] = platform.python_version()
    reports = {}
    path = Path(artifacts)
    path.mkdir(parents=True, exist_ok=True)
    cv = StratifiedKFold(config["training"]["cv_folds"], shuffle=True, random_state=seed)
    for kind, model in candidates.items():
        scores = cross_val_score(model, arrays["x_train"], arrays["y_train"], cv=cv, scoring="roc_auc", n_jobs=1)
        model.fit(arrays["x_train"], arrays["y_train"])
        vp = model.predict_proba(arrays["x_validation"])[:, 1]
        allowed = [t for t in np.linspace(.05, .8, 151)
                   if np.mean(vp[arrays["y_validation"] == 1] >= t) >= .85]
        threshold = float(max(allowed)) if allowed else .05
        bundle = export_model(model, kind)
        bundle.update({"threshold": threshold, "dataset_version": dataset["version"], "seed": seed,
                       "code_sha256": source_hash, "parameters": config["training"]})
        tp = predict(bundle, arrays["x_test"])
        parity = float(np.max(np.abs(tp - model.predict_proba(arrays["x_test"])[:, 1])))
        if parity > 1e-12:
            raise ValueError("JSON artifact inference differs from sklearn")
        model_hash = hashlib.sha256(canonical(bundle)).hexdigest()
        model_folder = path / model_hash
        model_folder.mkdir(exist_ok=True)
        model_path = model_folder / "model.json"
        payload = canonical(bundle)
        if model_path.exists():
            if model_path.read_bytes() != payload:
                raise ValueError("Existing model artifact is corrupted")
        else:
            with model_path.open("xb") as stream:
                stream.write(payload)
        report = {"run_id": uuid.uuid4().hex, "kind": kind, "dataset_version": dataset["version"],
                  "git_commit": commit.stdout.strip(), "git_dirty": bool(dirty.stdout.strip()),
                  "source_sha256": source_hash, "seed": seed, "parameters": config["training"],
                  "environment": environment, "model_sha256": model_hash,
                  "cv": {"folds": scores.tolist(), "auc_mean": float(scores.mean()),
                         "auc_std": float(scores.std())},
                  "validation": evaluate(arrays["y_validation"], vp, threshold),
                  "test": evaluate(arrays["y_test"], tp, threshold),
                  "parity_max_error": parity, "threshold": threshold,
                  "tracking": "local evidence only; MLflow integration not executed"}
        (model_folder / f"{report['run_id']}.report.json").write_bytes(canonical(report))
        reports[kind] = report
    selected = max(reports, key=lambda name: reports[name]["validation"]["auc"])
    return {"dataset_version": dataset["version"], "models": reports,
            "selected": selected, "selection_basis": "validation ROC-AUC only; test never selects model",
            "clinical_validity": False}


def gate(comparison, config, artifacts=None):
    decisions = {}
    for kind, report in comparison["models"].items():
        test = report["test"]
        limits = config["gate"]
        checks = {"auc": test["auc"] >= limits["min_auc"],
                  "sensitivity": test["sensitivity"] >= limits["min_sensitivity"],
                  "specificity": test["specificity"] >= limits["min_specificity"],
                  "brier": test["brier"] <= limits["max_brier"],
                  "parity": report["parity_max_error"] <= 1e-12}
        if artifacts is not None:
            version = report["model_sha256"]
            if len(version) != 64 or any(c not in "0123456789abcdef" for c in version):
                raise ValueError("Invalid model hash")
            payload = (Path(artifacts) / version / "model.json").read_bytes()
            checks["artifact_integrity"] = hashlib.sha256(payload).hexdigest() == version
        decisions[kind] = {"model_sha256": report["model_sha256"], "checks": checks,
                           "passed": all(checks.values())}
    return {"selected": comparison["selected"], "decisions": decisions, "criteria": config["gate"],
            "selected_passed": decisions[comparison["selected"]]["passed"],
            "promotion_performed": False}
