"""Explicit operator CLI; training never implicitly approves or deploys."""
import argparse
import json
import os

from .governance import Governance, verified_switch
from .settings import load_local
from .tracking import version_id


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['migrate', 'approve', 'deploy', 'rollback', 'reconcile', 'history'])
    parser.add_argument('--version')
    parser.add_argument('--actor')
    parser.add_argument('--api', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    if args.action in ('approve', 'deploy', 'rollback'):
        try:
            args.version = version_id(args.version)
        except ValueError as exc:
            parser.error(str(exc))
    load_local()
    gov = Governance()
    if args.action == 'migrate':
        gov.migrate()
        result = {'migrated': True}
    elif args.action == 'approve':
        result = gov.approve(args.version, args.actor, f'runtime/approval/{args.version}')
    elif args.action in ('deploy', 'rollback'):
        result = verified_switch(args.version, args.actor, 'runtime/deployment', args.api,
                                 os.environ['MEDMLOPS_API_TOKEN'], args.action == 'rollback')
    elif args.action == 'reconcile':
        result = {'reconciled': gov.reconcile()}
    else:
        result = gov.history()
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
