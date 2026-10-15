"""Execute available core lanes; explicitly exclude unexecuted integrations."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from medmlops.datasets import generate
from medmlops.monitor_windows import monitor

root = Path.cwd()
work = root / "runtime/verification-v2"
work.mkdir(parents=True, exist_ok=True)
outputs = []
for name, command in [
    ("pipeline", [sys.executable, "-m", "medmlops.pipeline", "all", "--work", str(work)]),
    ("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
]:
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    (work / f"{name}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    outputs.append({"name": name, "exit_code": result.returncode})
if not all(item["exit_code"] == 0 for item in outputs):
    print(json.dumps(outputs))
    raise SystemExit(1)
comparison = json.loads((work / "comparison.json").read_text())
selected = comparison["models"][comparison["selected"]]
bundle = json.loads((work / "candidates" / selected["model_sha256"] / "model.json").read_text())
policy = json.loads(Path("configs/params.json").read_text())["monitoring"]
reference, stable, shifted = generate(1000, 97), generate(1000, 99), generate(1000, 99, shifted=True)
reports = {"stable": monitor(bundle, reference, stable, policy),
           "shifted": monitor(bundle, reference, shifted, policy),
           "labelled": monitor(bundle, reference, stable, policy, labels=stable.target.to_numpy(), reference_metrics=selected["test"]),
           "regression": monitor(bundle, reference, stable, policy, labels=1-stable.target.to_numpy(), reference_metrics=selected["test"])}
assert not reports["stable"]["alerts"]
assert reports["shifted"]["prediction_drift"]["alert"]
assert any(a["type"] == "performance_degradation" for a in reports["regression"]["alerts"])
evidence = root / "docs/validation/evidence-v2"
evidence.mkdir(parents=True, exist_ok=True)
for name in ("pipeline.txt", "tests.txt", "comparison.json", "gate.json", "dataset.json", "validation.json"):
    (evidence / name).write_bytes((work / name).read_bytes())
(evidence / "monitoring.json").write_text(json.dumps(reports, indent=2), encoding="utf-8")
summary = {"executed_at": datetime.now(timezone.utc).isoformat(), "results": outputs,
           "core_passed": True, "full_platform_passed": False,
           "not_executed": ["DVC", "MLflow/PostgreSQL", "FastAPI/Uvicorn", "Evidently",
                            "Prometheus/Grafana", "Docker", "pytest/Ruff/pip-audit", "target deployment/rollback"]}
(evidence / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
