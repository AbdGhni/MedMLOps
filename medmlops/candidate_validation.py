"""Artifact and held-out evidence verification, independent of service integrations.

This executes actual v2 artifacts. It does not register, approve or deploy a model.
"""
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from .datasets import FEATURES, SCHEMA
from .experiments import evaluate, gate
from .scoring import predict


def finite_vector(value, size, name):
    if not isinstance(value, list) or len(value) != size:
        raise ValueError(f"Invalid {name} shape")
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) for v in value):
        raise ValueError(f"Invalid {name} numeric type")
    array = np.asarray(value, dtype=float)
    if not np.isfinite(array).all():
        raise ValueError(f"Nonfinite {name}")
    return array


def validate_structure(bundle):
    if not isinstance(bundle, dict) or bundle.get("schema") != SCHEMA or bundle.get("features") != list(FEATURES):
        raise ValueError("Unsupported artifact schema")
    threshold = bundle.get("threshold")
    if isinstance(threshold, bool) or not isinstance(threshold, (float, int)) or not 0 <= threshold <= 1:
        raise ValueError("Invalid model threshold")
    if bundle.get("kind") == "logistic":
        finite_vector(bundle.get("mean"), len(FEATURES), "mean")
        scales = finite_vector(bundle.get("scale"), len(FEATURES), "scale")
        if np.any(scales <= 0):
            raise ValueError("Model scales must be positive")
        finite_vector(bundle.get("coef"), len(FEATURES), "coef")
        finite_vector([bundle.get("intercept")], 1, "intercept")
        return
    trees = bundle.get("trees")
    if bundle.get("kind") != "forest" or not isinstance(trees, list) or not 1 <= len(trees) <= 512:
        raise ValueError("Unsupported or unbounded forest")
    for tree in trees:
        count = len(tree.get("left", []))
        if not 1 <= count <= 8191:
            raise ValueError("Invalid tree size")
        arrays = {name: finite_vector(tree.get(name), count, name)
                  for name in ("left", "right", "feature", "threshold", "positive_probability")}
        for name in ("left", "right", "feature"):
            if not np.equal(arrays[name], np.floor(arrays[name])).all():
                raise ValueError("Noninteger tree index")
        probabilities = arrays["positive_probability"]
        if np.any((probabilities < 0) | (probabilities > 1)):
            raise ValueError("Invalid leaf probability")
        for node in range(count):
            left, right, feature = (int(arrays[n][node]) for n in ("left", "right", "feature"))
            if left == -1 and right == -1:
                continue
            if not (node < left < count and node < right < count and 0 <= feature < len(FEATURES)):
                raise ValueError("Invalid or cyclic tree topology")


def verify_candidate(work, kind, actor):
    if not isinstance(actor, str) or not re.fullmatch(r"[A-Za-z0-9._@:-]{1,128}", actor):
        raise ValueError("Explicit actor identifier required; control characters are forbidden")
    work = Path(work)
    comparison = json.loads((work / "comparison.json").read_text())
    if kind not in ("logistic", "forest") or kind not in comparison["models"]:
        raise ValueError("Unknown candidate kind")
    report = comparison["models"][kind]
    version = report["model_sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", version):
        raise ValueError("Invalid candidate hash")
    path = work / "candidates" / version / "model.json"
    if path.stat().st_size > 64 * 1024 * 1024:
        raise ValueError("Artifact size limit exceeded")
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != version:
        raise ValueError("Candidate integrity failed")
    bundle = json.loads(payload)
    validate_structure(bundle)
    prepared = work / "prepared"
    manifest = json.loads((prepared / "manifest.json").read_text())
    if hashlib.sha256((prepared / "splits.npz").read_bytes()).hexdigest() != manifest["prepared_sha256"]:
        raise ValueError("Held-out dataset integrity failed")
    if not manifest["version"] == report["dataset_version"] == bundle["dataset_version"]:
        raise ValueError("Candidate/dataset provenance mismatch")
    if bundle["code_sha256"] != report["source_sha256"]:
        raise ValueError("Candidate/source provenance mismatch")
    if not re.fullmatch(r"[0-9a-f]{40}", report["git_commit"]):
        raise ValueError("Invalid Git provenance")
    with np.load(prepared / "splits.npz", allow_pickle=False) as arrays:
        ids = [set(arrays[f"ids_{s}"].tolist()) for s in ("train", "validation", "test")]
        if ids[0] & ids[1] or ids[0] & ids[2] or ids[1] & ids[2]:
            raise ValueError("Held-out subject overlap")
        x, y = arrays["x_test"], arrays["y_test"]
        if not np.isin(y, [0, 1]).all() or len(np.unique(y)) != 2:
            raise ValueError("Invalid held-out labels")
        measured = evaluate(y, predict(bundle, x), bundle["threshold"])
    matching_metrics = all(np.isclose(measured[name], report["test"][name], rtol=0, atol=1e-12)
                           for name in ("auc", "pr_auc", "average_precision", "sensitivity", "specificity", "f1", "brier"))
    matching_confusion = measured["confusion"] == report["test"]["confusion"]
    return {"actor": actor, "timestamp": datetime.now(timezone.utc).isoformat(), "model_sha256": version,
            "dataset_version": manifest["version"], "git_commit": report["git_commit"],
            "checks": {"artifact_structure": True, "dataset_integrity": True,
                       "metrics_recomputed_match": bool(matching_metrics),
                       "confusion_recomputed_match": matching_confusion,
                       "clean_training_commit": report["git_dirty"] is False},
            "recomputed_test": measured, "promotion_performed": False,
            "approval_performed": False, "integration": "offline artifact validation, not MLflow/PG"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work", default="runtime/verification-v2")
    parser.add_argument("--actor", required=True)
    parser.add_argument("--config", default="configs/params.json")
    parser.add_argument("--kind", choices=["logistic", "forest"], default="logistic")
    args = parser.parse_args(argv)
    result = verify_candidate(args.work, args.kind, args.actor)
    comparison = json.loads((Path(args.work) / "comparison.json").read_text())
    config = json.loads(Path(args.config).read_text())
    result["quality_checks"] = gate(comparison, config, Path(args.work) / "candidates")["decisions"][args.kind]["checks"]
    result["passed"] = all(result["checks"].values()) and all(result["quality_checks"].values())
    print(json.dumps(result, indent=2))
    return 0 if result["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
