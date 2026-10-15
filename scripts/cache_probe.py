"""Reversible integrity fault injection in this demo's serving cache only."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['corrupt', 'restore'])
    parser.add_argument('--version', required=True, type=int)
    args = parser.parse_args()
    root = Path('/app/runtime/serving').resolve()
    path = root / str(args.version) / 'bundle' / 'model.json'
    backup = path.with_suffix('.probe-backup')
    if args.action == 'corrupt':
        if backup.exists():
            raise ValueError('Probe backup already exists')
        backup.write_bytes(path.read_bytes())
        path.write_bytes(b'{}')
    else:
        path.write_bytes(backup.read_bytes())
        backup.unlink()
    print('Serving cache probe ' + args.action + ' completed')


if __name__ == '__main__':
    main()
