"""Local publication inventory; never emits secret values or changes Git history."""
import hashlib
import importlib.metadata as metadata
import json
import re
import subprocess
from pathlib import Path

from packaging.requirements import Requirement


def main():
    output = Path('docs/validation/phase5')
    output.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
    revisions = subprocess.check_output(['git', 'rev-list', '--all']).decode().splitlines()
    secrets = [line.split('=', 1)[1] for line in Path('.env').read_text().splitlines()
               if '=' in line and not line.startswith('#') and len(line.split('=', 1)[1]) >= 16]
    findings = []
    patterns = [rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
                rb'gh[pousr]_[A-Za-z0-9]{30,}', rb'AKIA[0-9A-Z]{16}']
    blobs = subprocess.check_output(['git', 'rev-list', '--objects', '--all']).decode().splitlines()
    for entry in blobs:
        oid, _, path = entry.partition(' ')
        if not path:
            continue
        if subprocess.check_output(['git', 'cat-file', '-t', oid]).strip() != b'blob':
            continue
        data = subprocess.check_output(['git', 'cat-file', 'blob', oid])
        if any(secret.encode() in data for secret in secrets) or any(re.search(p, data) for p in patterns):
            findings.append({'path': path, 'object': oid})
    current = sorted(set(tracked + [str(p).replace('\\', '/') for root in ('medmlops', 'scripts', 'docs', '.github', 'tests')
                                  for p in Path(root).rglob('*') if p.is_file() and '__pycache__' not in p.parts]))
    current_findings = []
    for name in current:
        path = Path(name)
        if not path.is_file() or name.endswith('release_inventory.py'):
            continue
        data = path.read_bytes()
        if any(secret.encode() in data for secret in secrets) or any(re.search(p, data) for p in patterns):
            current_findings.append(name)
    packages = []
    edges = []
    for dist in sorted(metadata.distributions(), key=lambda d: d.metadata['Name'].lower()):
        name = dist.metadata['Name']
        packages.append({'name': name, 'version': dist.version,
                         'license_expression': dist.metadata.get('License-Expression'),
                         'license': dist.metadata.get('License'),
                         'license_classifiers': [c for c in dist.metadata.get_all('Classifier', []) if c.startswith('License ::')]})
        for raw in dist.requires or []:
            req = Requirement(raw)
            if not req.marker or req.marker.evaluate():
                edges.append({'from': name, 'to': req.name, 'requirement': raw})
    (output / 'dependency-inventory.json').write_text(json.dumps({'packages': packages, 'active_edges': edges}, indent=2), encoding='utf-8')
    result = {'history_commits_scanned': len(revisions), 'history_findings': findings,
              'working_tree_findings': current_findings,
              'scope': 'known local .env values, private key markers, GitHub/AWS token patterns; not a complete entropy scanner',
              'tracked_files': len([p for p in tracked if p]),
              'files': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in current
                        if Path(p).is_file() and not p.startswith('docs/validation/phase5/')}}
    (output / 'release-inventory.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'files'}, indent=2))
    return int(bool(findings or current_findings))


if __name__ == '__main__':
    raise SystemExit(main())
