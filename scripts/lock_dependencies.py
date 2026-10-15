"""Pin the resolved environment with verified PyPI distribution hashes."""
import importlib.metadata
import json
import urllib.request
from pathlib import Path


def main():
    lines = ['# Resolved on Python 3.12.4; all release distribution SHA256 hashes from PyPI.']
    packages = sorted((d.metadata['Name'], d.version) for d in importlib.metadata.distributions()
                      if d.metadata['Name'].lower() not in ('pip', 'medmlops'))
    packages += [('gunicorn', '26.2.0'), ('uvloop', '0.23.0')]
    for name, version in packages:
        with urllib.request.urlopen(f'https://pypi.org/pypi/{name}/{version}/json', timeout=30) as response:
            data = json.load(response)
        hashes = sorted({f['digests']['sha256'] for f in data['urls'] if not f['yanked']})
        if not hashes:
            raise ValueError(f'No verified distributions: {name}')
        marker = '; sys_platform == "win32"' if name.lower() == 'pywin32' else ''
        if name in ('gunicorn', 'uvloop'):
            marker = '; sys_platform != "win32"'
        lines.append(f'{name}=={version}{marker} \\')
        lines.extend('    --hash=sha256:' + h + (' \\' if i < len(hashes) - 1 else '')
                     for i, h in enumerate(hashes))
    Path('requirements-target.lock').write_text('\n'.join(lines) + '\n')
    print(f'Locked {len(packages)} distributions with PyPI hashes')


if __name__ == '__main__':
    main()
