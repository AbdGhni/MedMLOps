"""Save actual execution evidence. Any failed check produces a nonzero exit."""
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
evidence = root / "docs" / "evidence"
evidence.mkdir(parents=True, exist_ok=True)
commands = [
    ("tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"]),
    ("demo", [sys.executable, "-m", "medmlops.cli", "--root", "runtime/validated", "demo"]),
    ("batch", [sys.executable, "-m", "medmlops.cli", "--root", "runtime/validated", "batch",
               "examples/record.json", "runtime/validated/batch-output.json"]),
]
# Batch deliberately refuses overwrite: use a unique evidence output on repeat runs.
commands[2][1][-1] = "runtime/validated/batch-" + datetime.now().strftime("%Y%m%d%H%M%S%f") + ".json"
results = []
for name, command in commands:
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    (evidence / f"{name}.txt").write_text(result.stdout + result.stderr, encoding="utf-8")
    if name == "demo" and result.returncode == 0:
        (evidence / "demo.json").write_text(result.stdout, encoding="utf-8")
    results.append({"check": name, "exit_code": result.returncode})
summary = {"executed_at": datetime.now(timezone.utc).isoformat(), "platform": platform.platform(),
           "python": platform.python_version(), "results": results,
           "passed": all(r["exit_code"] == 0 for r in results)}
(evidence / "validation.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
sys.exit(0 if summary["passed"] else 1)
