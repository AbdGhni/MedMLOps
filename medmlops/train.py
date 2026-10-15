"""Deterministic train/validation/test pipeline with explicit quality gates."""
import hashlib
import importlib.metadata
import platform
from pathlib import Path

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from .data import FEATURES, SCHEMA_VERSION, fingerprint, generate
from .model import predict


def metrics(y, p, threshold):
    tn, fp, fn, tp = confusion_matrix(y, p >= threshold, labels=[0, 1]).ravel()
    return {"auc": float(roc_auc_score(y, p)),
            "average_precision": float(average_precision_score(y, p)),
            "brier": float(brier_score_loss(y, p)),
            "sensitivity": float(tp / max(tp + fn, 1)),
            "specificity": float(tn / max(tn + fp, 1)),
            "confusion": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
            "samples": len(y), "positives": int(y.sum())}


def quality_gate(test, slices):
    checks = {"required_slices": set(slices) == {"age_under_65", "age_65_plus"},
              "auc_ge_0.78": test["auc"] >= 0.78,
              "sensitivity_ge_0.75": test["sensitivity"] >= 0.75,
              "specificity_ge_0.40": test["specificity"] >= 0.4,
              "brier_le_0.20": test["brier"] <= 0.2,
              "slice_support": all(s["samples"] >= 50 and s["positives"] >= 20 for s in slices.values()),
              "slice_sensitivity_ge_0.65": all(s["sensitivity"] >= 0.65 for s in slices.values())}
    return checks, all(checks.values())


def train(store, seed=42, n=4000):
    x, y = generate(n, seed)
    indices = np.arange(n)
    training, holdout = train_test_split(indices, test_size=0.4, random_state=seed, stratify=y)
    validation, testing = train_test_split(holdout, test_size=0.5, random_state=seed, stratify=y[holdout])
    pipeline = make_pipeline(StandardScaler(), LogisticRegression(random_state=seed, max_iter=1000))
    pipeline.fit(x[training], y[training])
    vp = pipeline.predict_proba(x[validation])[:, 1]
    candidates = np.linspace(0.05, 0.8, 151)
    admissible = [t for t in candidates if np.mean(vp[y[validation] == 1] >= t) >= 0.85]
    threshold = float(max(admissible)) if admissible else 0.05
    scaler, classifier = pipeline.steps[0][1], pipeline.steps[1][1]
    reference = {}
    for j, name in enumerate(FEATURES):
        edges = np.unique(np.quantile(x[training, j], np.linspace(0.1, 0.9, 9)))
        counts = np.histogram(x[training, j], bins=[-np.inf, *edges, np.inf])[0]
        reference[name] = {"edges": edges.tolist(),
                           "proportions": ((counts + 0.5) / (counts.sum() + len(counts) * 0.5)).tolist()}
    bundle = {"schema": SCHEMA_VERSION, "features": list(FEATURES),
              "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
              "coef": classifier.coef_[0].tolist(), "intercept": float(classifier.intercept_[0]),
              "threshold": threshold, "reference": reference,
              "seed": seed, "dataset_sha256": fingerprint(x, y),
              "algorithm": "StandardScaler + LogisticRegression(C=1, solver=lbfgs)",
              "code_sha256": hashlib.sha256(b"".join(
                  (Path(__file__).parent / name).read_bytes()
                  for name in ("data.py", "model.py", "train.py"))).hexdigest()}
    p = predict(bundle, x[testing])
    parity = float(np.max(np.abs(p - pipeline.predict_proba(x[testing])[:, 1])))
    if parity > 1e-12:
        raise ValueError("Train/serve parity failed")
    test = metrics(y[testing], p, threshold)
    slices = {}
    for name, mask in {"age_under_65": x[testing, 0] < 65,
                       "age_65_plus": x[testing, 0] >= 65}.items():
        slices[name] = metrics(y[testing][mask], p[mask], threshold)
    rng = np.random.default_rng(seed)
    aucs = []
    for _ in range(200):
        sample = rng.integers(0, len(testing), len(testing))
        if len(np.unique(y[testing][sample])) == 2:
            aucs.append(roc_auc_score(y[testing][sample], p[sample]))
    checks, passed = quality_gate(test, slices)
    calibration = []
    for lo, hi in zip(np.linspace(0, 1, 11)[:-1], np.linspace(0, 1, 11)[1:], strict=True):
        mask = (p >= lo) & (p < hi if hi < 1 else p <= hi)
        if mask.any():
            calibration.append({"lower": float(lo), "upper": float(hi), "n": int(mask.sum()),
                                "mean_probability": float(p[mask].mean()),
                                "observed_fraction": float(y[testing][mask].mean())})
    baseline_probability = float(y[training].mean())
    report = {"seed": seed, "n": n, "data": "synthetic; no clinical validity",
              "code_sha256": bundle["code_sha256"], "algorithm": bundle["algorithm"],
              "dataset_sha256": bundle["dataset_sha256"], "threshold": threshold,
              "split": {name: {"count": len(idx), "sha256": fingerprint(x[idx], y[idx])}
                        for name, idx in [("train", training), ("validation", validation), ("test", testing)]},
              "validation": metrics(y[validation], vp, threshold), "test": test,
              "auc_bootstrap_95_ci": np.quantile(aucs, [0.025, 0.975]).tolist(),
              "slices": slices, "checks": checks, "passed": passed,
              "baseline": {"auc": 0.5, "brier": float(brier_score_loss(
                  y[testing], np.full(len(testing), baseline_probability)))},
              "calibration": calibration,
              "train_serve_max_error": parity,
              "environment": {"python": platform.python_version(),
                              **{name: importlib.metadata.version(name) for name in
                                 ("numpy", "scipy", "scikit-learn", "Flask")}}}
    version = store.save(bundle, report)
    return {"version": version, "report": report}
