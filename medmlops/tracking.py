"""Real MLflow tracking/registry adapter for verified v2 numeric bundles."""
import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

from mlflow import MlflowClient
from mlflow.entities import Metric, Param
from mlflow.models import Model

from .candidate_validation import validate_structure, verify_candidate
from .experiments import gate
from .settings import load_local, tracking_uri

# MLflow prints run links containing emoji; managed Windows terminals may use cp1252.
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
os.environ.setdefault('MLFLOW_HTTP_REQUEST_TIMEOUT', '15')
os.environ.setdefault('MLFLOW_HTTP_REQUEST_MAX_RETRIES', '1')

MODEL_NAME = 'synthetic-event-v2'


def version_id(version):
    """Registry versions are positive integers, never filesystem paths."""
    value = str(version)
    if not re.fullmatch(r'[1-9][0-9]{0,18}', value):
        raise ValueError('Invalid registry version')
    return value


def publish(work, actor, config='configs/params.json', experiment='medmlops-v2'):
    work = Path(work)
    comparison = json.loads((work / 'comparison.json').read_text())
    policy = json.loads(Path(config).read_text())
    client = MlflowClient(tracking_uri=tracking_uri())
    existing = client.get_experiment_by_name(experiment)
    experiment_id = existing.experiment_id if existing else client.create_experiment(experiment)
    if not client.search_registered_models(filter_string=f"name = '{MODEL_NAME}'"):
        client.create_registered_model(MODEL_NAME)
    versions = {}
    for kind, report in comparison['models'].items():
        evidence = verify_candidate(work, kind, actor)
        quality = gate(comparison, policy, work / 'candidates')['decisions'][kind]
        # Tracking records rejected candidates too; approval remains a separate operation.
        tags = {key: str(report[key]) for key in (
            'dataset_version', 'git_commit', 'git_dirty', 'source_sha256', 'model_sha256')}
        tags.update({'kind': kind, 'actor': actor, 'gate_passed': str(quality['passed'])})
        run = client.create_run(experiment_id, tags=tags)
        run_id = run.info.run_id
        try:
            metrics = [Metric(f'{split}_{k}', float(v), 0, 0)
                       for split in ('validation', 'test') for k, v in report[split].items()
                       if isinstance(v, (int, float))]
            metrics += [Metric('cv_auc_mean', report['cv']['auc_mean'], 0, 0),
                        Metric('parity_max_error', report['parity_max_error'], 0, 0)]
            params = [Param(k, str(v)) for k, v in report['parameters'].items()]
            client.log_batch(run_id, metrics=metrics, params=params)
            folder = work / 'candidates' / report['model_sha256']
            client.log_artifact(run_id, str(folder / 'model.json'), 'bundle')
            staging = work / 'publication' / run_id
            staging.mkdir(parents=True)
            for name, content in (('report.json', report), ('verification.json', evidence), ('config.json', policy)):
                local = staging / name
                local.write_text(json.dumps(content, indent=2))
                client.log_artifact(run_id, str(local), 'bundle')
            metadata = Model()
            metadata.add_flavor('python_function', loader_module='medmlops.pyfunc',
                                data='model.json', python_version=platform.python_version())
            metadata.save(str(staging / 'MLmodel'))
            client.log_artifact(run_id, str(staging / 'MLmodel'), 'bundle')
            client.log_artifact(run_id, str(work / 'prepared' / 'manifest.json'), 'data')
            # MLflow Registry points to the non-executable numeric artifact directory.
            version = client.create_model_version(MODEL_NAME, f'runs:/{run_id}/bundle', run_id,
                                                  tags={'model_sha256': report['model_sha256'],
                                                        'lifecycle': 'candidate'})
            client.set_registered_model_alias(MODEL_NAME, f'candidate_{kind}', version.version)
            client.set_terminated(run_id, 'FINISHED')
            versions[kind] = {'version': version.version, 'run_id': run_id,
                              'model_sha256': report['model_sha256']}
        except Exception:
            client.set_terminated(run_id, 'FAILED')
            raise
    result = {'model_name': MODEL_NAME, 'selected': comparison['selected'], 'versions': versions}
    (work / 'tracking.json').write_text(json.dumps(result, indent=2))
    return result


def fetch(version, destination):
    version = version_id(version)
    client = MlflowClient(tracking_uri=tracking_uri())
    registered = client.get_model_version(MODEL_NAME, str(version))
    if not registered.run_id:
        raise ValueError('Registry version has no tracking run')
    path = Path(destination)
    path.mkdir(parents=True, exist_ok=True)
    bundle_path = path / 'bundle'
    bundle_path.mkdir(exist_ok=True)
    files = {}
    for name in ('model.json', 'report.json', 'verification.json', 'config.json'):
        downloaded = client.download_artifacts(registered.run_id, f'bundle/{name}', str(bundle_path))
        files[name] = json.loads(Path(downloaded).read_text())
    payload = (path / 'bundle' / 'model.json').read_bytes()
    expected = registered.tags['model_sha256']
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError('Registry artifact integrity failed')
    validate_structure(files['model.json'])
    return files, expected, registered.run_id


def server():
    load_local()
    password = os.environ['MLFLOW_DB_PASSWORD']
    host = os.getenv('POSTGRES_HOST', 'postgres')
    port = os.getenv('POSTGRES_PORT', '5432')
    uri = f'postgresql+psycopg2://mlflow:{password}@{host}:{port}/mlflow'
    subprocess.run([sys.executable, '-m', 'mlflow', 'server', '--host', '0.0.0.0',
                    '--port', '5000', '--backend-store-uri', uri,
                    '--artifacts-destination', '/app/runtime/mlartifacts',
                    '--serve-artifacts', '--allowed-hosts', 'mlflow:5000,localhost:*,127.0.0.1:*'],
                   check=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['server', 'publish'])
    parser.add_argument('--work', default='data')
    parser.add_argument('--actor')
    args = parser.parse_args()
    if args.action == 'server':
        server()
    else:
        print(json.dumps(publish(args.work, args.actor), indent=2))


if __name__ == '__main__':
    main()
