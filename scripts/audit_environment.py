"""Read-only inventory with bounded output and no environment credentials."""
import importlib.metadata
import json
import os
import platform
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
installed = {d.metadata["Name"].lower(): d.version for d in importlib.metadata.distributions()}
names = ["numpy", "pandas", "scikit-learn", "scipy", "pydantic", "fastapi", "uvicorn", "mlflow",
         "dvc", "evidently", "pytest", "ruff", "mypy", "pip-audit", "prometheus-client", "psycopg"]
commands = [["git", "status", "--short"], ["git", "rev-parse", "HEAD"],
            ["docker", "version", "--format", "{{.Client.Version}} {{.Server.Version}}"],
            ["docker", "info", "--format", "{{.NCPU}} {{.MemTotal}}"],
            ["docker", "compose", "version"]]
observations = []
for command in commands:
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, text=True, timeout=20)
        observations.append({"command": command, "exit_code": result.returncode,
                             "stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    except (OSError, subprocess.TimeoutExpired) as error:
        observations.append({"command": command, "error": type(error).__name__})
report = {"executed_at": datetime.now(timezone.utc).isoformat(), "repository": str(root),
          "platform": platform.platform(), "python": platform.python_version(),
          "logical_cpus": os.cpu_count(), "disk_free_bytes": shutil.disk_usage(root).free,
          "docker_memory": "unknown unless docker info succeeds", "pip_no_index": os.environ.get("PIP_NO_INDEX"),
          "packages": {n: installed.get(n, "NOT_INSTALLED") for n in names}, "commands": observations}
target = root / "docs/validation/environment.json"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps({"evidence": str(target), "packages": report["packages"]}, indent=2))
