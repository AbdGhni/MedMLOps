"""Run local release lanes, preserve prior evidence and retain redacted logs."""
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from medmlops.settings import load_local


def main():
    load_local()
    root = Path('runtime/phase5-execution')
    root.mkdir(parents=True, exist_ok=True)
    os.environ['MEDMLOPS_EVIDENCE_DIR'] = str(root)
    python = sys.executable
    commands = [
        ('quality', [python, '-m', 'scripts.record_phase4_quality']),
        ('unittest', [python, '-m', 'unittest', 'discover', '-s', 'tests', '-v']),
        ('pipeline', [python, '-m', 'medmlops.pipeline', 'all', '--work', 'runtime/phase4']),
        ('compose-build-start', ['docker', 'compose', 'up', '--build', '-d', '--wait', '--wait-timeout', '240']),
        ('dvc', [python, '-m', 'scripts.check_dvc']),
        ('tracking', [python, '-m', 'scripts.check_tracking']),
        ('end-to-end', [python, '-m', 'scripts.validate_phase4']),
        ('dependency-audit', [python, '-m', 'pip_audit', '--cache-dir', 'runtime/pip-audit-cache',
                              '--format', 'json', '--output', str(root / 'dependency-audit.json')]),
    ]
    dirty = subprocess.check_output(['git', 'status', '--porcelain']).decode()
    if dirty.strip():
        raise RuntimeError('Commit source and documentation before release validation')
    results = []
    for name, command in commands:
        print(f'Running {name}', flush=True)
        completed = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
        log = completed.stdout + completed.stderr
        for key in ('POSTGRES_PASSWORD', 'MLFLOW_DB_PASSWORD', 'GOVERNANCE_DB_PASSWORD',
                    'SERVING_DB_PASSWORD', 'MEDMLOPS_API_TOKEN', 'GRAFANA_PASSWORD'):
            value = os.environ.get(key)
            if value:
                log = log.replace(value, '[REDACTED]')
        (root / f'{name}.log').write_text(log, encoding='utf-8')
        results.append({'lane': name, 'exit_code': completed.returncode, 'command': command})
        (root / 'execution.json').write_text(json.dumps({
            'executed_at': datetime.now(UTC).isoformat(),
            'commit': subprocess.check_output(['git', 'rev-parse', 'HEAD']).decode().strip(),
            'clean_at_start': True, 'results': results}, indent=2), encoding='utf-8')
        print(f'{name}: exit {completed.returncode}', flush=True)
        if completed.returncode and name != 'dependency-audit':
            return completed.returncode
    return results[-1]['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
