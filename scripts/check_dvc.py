"""Real DVC reproduction lane; all subprocess logs retained and failures raised."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def main():
    os.environ['DVC_NO_ANALYTICS'] = '1'
    os.environ['ITERATIVE_DO_NOT_TRACK'] = 'do-not-track'
    for key, directory in (('DVC_SITE_CACHE_DIR', 'dvc-site-cache'),
                           ('DVC_GLOBAL_CONFIG_DIR', 'dvc-global'),
                           ('DVC_SYSTEM_CONFIG_DIR', 'dvc-system')):
        os.environ[key] = str(Path('runtime', directory).resolve())
    os.environ['PATH'] = str(Path(sys.executable).parent) + os.pathsep + os.environ['PATH']
    executable = str(Path(sys.executable).parent / ('dvc.exe' if os.name == 'nt' else 'dvc'))
    evidence = Path(os.getenv('MEDMLOPS_EVIDENCE_DIR', 'docs/validation/phase4'))
    evidence.mkdir(parents=True, exist_ok=True)

    def command(name, *args):
        result = subprocess.run([executable, *args], capture_output=True, text=True, encoding='utf-8', errors='replace')
        (evidence / f'dvc-{name}.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(f'DVC {name} failed: see evidence log')
        return result.stdout

    command('remote', 'remote', 'add', '-d', '-f', 'local', 'runtime/dvc-remote')
    command('cache', 'config', 'cache.type', 'copy')
    command('repro', 'repro')

    def identities():
        comparison = json.loads(Path('data/comparison.json').read_text())
        return {'dataset': comparison['dataset_version'],
                'models': {k: r['model_sha256'] for k, r in comparison['models'].items()}}

    first = identities()
    command('push', 'push')
    noop = command('noop', 'repro')
    assert 'unchanged' in noop.lower() or 'up to date' in noop.lower()
    command('force', 'repro', '--force')
    assert identities() == first
    params = Path('configs/params.json')
    original = params.read_bytes()
    original_lock = Path('dvc.lock').read_bytes()
    changed = json.loads(original)
    changed['dataset']['seed'] += 1
    try:
        params.write_text(json.dumps(changed, indent=2) + '\n')
        command('changed-seed', 'repro')
        assert identities()['dataset'] != first['dataset']
    finally:
        params.write_bytes(original)
        Path('dvc.lock').write_bytes(original_lock)
        command('older-checkout', 'checkout', '--force')
    assert identities() == first
    command('status', 'status')
    result = {'passed': True, 'identities': first, 'forced_reproduction_identical': True,
              'changed_seed_invalidates': True, 'older_dataset_checkout': True,
              'lock_sha256': hashlib.sha256(Path('dvc.lock').read_bytes()).hexdigest()}
    (evidence / 'dvc.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
