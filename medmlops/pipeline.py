"""Explicit generate/validate/prepare/train/evaluate stages for DVC and local use."""
import argparse
import json
from pathlib import Path

from .data import canonical
from .datasets import SCHEMA, load_snapshot, snapshot, validate
from .experiments import gate, prepare, run


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["generate", "validate", "prepare", "train", "evaluate", "all"])
    parser.add_argument("--config", default="configs/params.json")
    parser.add_argument("--work", default="runtime/v2")
    args = parser.parse_args(argv)
    config = json.loads(Path(args.config).read_text())
    if config["dataset"]["schema"] != SCHEMA:
        raise ValueError("Unsupported dataset schema")
    if config["split"] != {"train_fraction": .6, "validation_fraction": .2}:
        raise ValueError("Only the documented 60/20/20 split is implemented")
    work = Path(args.work)
    stages = ["generate", "validate", "prepare", "train", "evaluate"] if args.stage == "all" else [args.stage]
    for stage in stages:
        if stage == "generate":
            result = snapshot(work / "raw", config["dataset"]["n"], config["dataset"]["seed"])
            write(work / "dataset.json", result)
        elif stage in ("validate", "prepare"):
            version = json.loads((work / "dataset.json").read_text())["version"]
            frame, _ = load_snapshot(work / "raw", version)
            if stage == "validate":
                result = {**validate(frame), "dataset_version": version}
                write(work / "validation.json", result)
            else:
                if not json.loads((work / "validation.json").read_text())["passed"]:
                    raise ValueError("Dataset has not passed validation")
                result = prepare(work / "raw", version, work / "prepared", config["training"]["seed"])
        elif stage == "train":
            result = run(work / "prepared", work / "candidates", config)
            write(work / "comparison.json", result)
        else:
            comparison = json.loads((work / "comparison.json").read_text())
            result = gate(comparison, config, work / "candidates")
            write(work / "gate.json", result)
        print(json.dumps({"stage": stage, "result": result}, indent=2))
        if stage == "evaluate" and not result["selected_passed"]:
            return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
