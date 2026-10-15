"""Record actual local quality checks and evidence hashes without credentials."""
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path


def main():
    destination = Path(os.getenv('MEDMLOPS_EVIDENCE_DIR', 'docs/validation/phase4'))
    destination.mkdir(parents=True, exist_ok=True)
    commands = {
        'pip-check': [sys.executable, '-m', 'pip', 'check'],
        'tests': [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider'],
        'lint': [sys.executable, '-m', 'ruff', 'check', 'medmlops', 'scripts', 'tests'],
        'typing': [sys.executable, '-m', 'mypy', '--check-untyped-defs', '--ignore-missing-imports',
                   'medmlops/settings.py', 'medmlops/governance.py', 'medmlops/tracking.py',
                   'medmlops/serving.py', 'medmlops/monitoring.py', 'medmlops/pyfunc.py'],
    }
    checks = {}
    for name, command in commands.items():
        completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
        (destination / f'{name}.txt').write_text(completed.stdout + completed.stderr, encoding='utf-8')
        checks[name] = {'exit_code': completed.returncode, 'command': [Path(sys.executable).name, *command[1:]]}
        if completed.returncode:
            raise RuntimeError(f'{name} failed: inspect recorded evidence')
    report = {'timestamp': datetime.now(UTC).isoformat(), 'python': platform.python_version(),
              'checks': checks, 'versions': {name: importlib.metadata.version(name) for name in
              ('mlflow', 'dvc', 'fastapi', 'uvicorn', 'evidently', 'psycopg', 'prometheus-client')},
              'hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.glob('*.json')},
              'browser_rendering': 'not verified: no enabled computer-use browser surface',
              'github_actions_execution': 'not run; no publication authorized'}
    (destination / 'quality.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
