"""Real full-stack lifecycle acceptance. Requires running Compose services."""
import hashlib
import json
import os
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import numpy as np
import psycopg
from mlflow import MlflowClient

from medmlops.data import canonical
from medmlops.datasets import FEATURES, generate
from medmlops.experiments import evaluate
from medmlops.governance import Governance, verified_switch
from medmlops.monitoring import inspect_window
from medmlops.scoring import predict
from medmlops.settings import load_local, tracking_uri
from medmlops.tracking import MODEL_NAME, fetch, publish

ROOT = Path('runtime/phase4')
EVIDENCE = Path(os.getenv('MEDMLOPS_EVIDENCE_DIR', 'docs/validation/phase4'))


def wait_for(check, seconds=90):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                return result
        except (httpx.HTTPError, KeyError, AssertionError):
            pass
        time.sleep(2)
    raise AssertionError('Service check timed out')


def main():
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    load_local()
    token = os.environ['MEDMLOPS_API_TOKEN']
    headers = {'Authorization': f'Bearer {token}'}
    api = 'http://127.0.0.1:8000'
    gov = Governance()
    gov.migrate()
    tracking = json.loads((ROOT / 'tracking.json').read_text())
    first = tracking['versions'][tracking['selected']]['version']
    second_kind = next(k for k in tracking['versions'] if k != tracking['selected'])
    second = tracking['versions'][second_kind]['version']
    actor = 'local-demo-operator'
    gov.approve(second, actor, ROOT / 'second')
    assert httpx.get(api + '/ready').status_code == 401
    first_deploy = verified_switch(first, actor, ROOT / 'deploy', api, token)
    record = generate(500).iloc[0][list(FEATURES)].to_dict()
    for key in ('sex_code', 'prior_event'):
        record[key] = int(record[key])
    body = {'records': [record]}
    response = httpx.post(api + '/predict', headers=headers, json=body)
    response.raise_for_status()
    bundle, _, _ = fetch(first, ROOT / 'e2e-download')
    expected = predict(bundle['model.json'], np.array([[record[f] for f in FEATURES]]))[0]
    assert abs(response.json()['probabilities'][0] - expected) <= 1e-12
    assert httpx.post(api + '/predict', headers=headers, json={'records': [{**record, 'patient_name': 'private'}]}).status_code == 422
    assert httpx.post(api + '/predict', headers=headers, content=b'x' * (1024 * 1024 + 1)).status_code == 413

    # Register an actually deficient numeric model; metrics are recomputed, not invented.
    bad = ROOT / 'bad'
    (bad / 'prepared').mkdir(parents=True, exist_ok=True)
    for name in ('manifest.json', 'splits.npz'):
        shutil.copyfile(ROOT / 'prepared' / name, bad / 'prepared' / name)
    model = dict(bundle['model.json'])
    model['coef'] = [0.0] * len(FEATURES)
    model['intercept'] = 0.0
    digest = hashlib.sha256(canonical(model)).hexdigest()
    folder = bad / 'candidates' / digest
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'model.json').write_bytes(canonical(model))
    report = dict(bundle['report.json'])
    report['model_sha256'] = digest
    with np.load(bad / 'prepared' / 'splits.npz', allow_pickle=False) as arrays:
        for split in ('test', 'validation'):
            report[split] = evaluate(arrays[f'y_{split}'], predict(model, arrays[f'x_{split}']), model['threshold'])
    (bad / 'comparison.json').write_bytes(canonical({'selected': 'logistic', 'models': {'logistic': report}}))
    bad_tracking = publish(bad, actor, experiment='phase4-rejected-model')
    bad_version = bad_tracking['versions']['logistic']['version']
    try:
        gov.approve(bad_version, actor, bad / 'download')
    except ValueError:
        pass
    else:
        raise AssertionError('Deficient candidate approved')
    try:
        gov.switch(bad_version, actor)
    except ValueError:
        pass
    else:
        raise AssertionError('Rejected candidate deployed')
    assert gov.active()['version'] == str(first)
    active = gov.active()
    try:
        gov.switch(second, actor, expected_generation=active['generation'] - 1)
    except ValueError:
        pass
    else:
        raise AssertionError('Stale concurrent switch accepted')
    # API credentials cannot mutate the deployment pointer or audit history.
    with psycopg.connect(host='127.0.0.1', port=5433, dbname='governance', user='serving',
                         password=os.environ['SERVING_DB_PASSWORD']) as conn:
        try:
            conn.execute('UPDATE deployment SET version=NULL WHERE id=1')
        except psycopg.errors.InsufficientPrivilege:
            conn.rollback()
        else:
            raise AssertionError('Serving role can deploy')

    # Transaction, concurrent audit, and immutable event protection.
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda i: gov.event(actor, 'concurrency_probe', details={'index': i}), range(8)))
    try:
        with gov.connect() as conn:
            conn.execute("UPDATE events SET actor='forged' WHERE id=(SELECT min(id) FROM events)")
    except Exception as exc:
        assert 'append-only audit' in str(exc)
    else:
        raise AssertionError('Audit update accepted')

    # A separately approved challenger can be deployed; drift never promotes a model.
    second_deploy = verified_switch(second, actor, ROOT / 'deploy', api, token)
    selected_bundle, _, _ = fetch(second, ROOT / 'monitor-download')
    model = selected_bundle['model.json']
    policy = json.loads(Path('configs/params.json').read_text())['monitoring']
    reference = generate(1000, 42)
    stable = inspect_window(model, reference, reference.copy(), policy, ROOT / 'reports', gov, actor, second)
    assert not stable['alerts']
    shifted = inspect_window(model, reference, generate(1000, 999, shifted=True), policy,
                             ROOT / 'reports', gov, actor, second)
    assert any(a['type'] == 'data_drift' for a in shifted['alerts'])
    assert any(a['type'] == 'prediction_drift' for a in shifted['alerts'])
    inverted = 1 - reference.target.to_numpy()
    measured = evaluate(reference.target.to_numpy(), predict(model, reference[list(FEATURES)].to_numpy()), model['threshold'])
    degraded = inspect_window(model, reference, reference.copy(), policy, ROOT / 'reports', gov, actor,
                              second, inverted, measured)
    assert any(a['type'] == 'performance_degradation' for a in degraded['alerts'])
    assert gov.active()['version'] == str(second)
    prom = 'http://127.0.0.1:9090'

    def query(expression):
        result = httpx.get(prom + '/api/v1/query', params={'query': expression}).json()
        assert result['status'] == 'success'
        return result['data']['result']

    scrape = wait_for(lambda: query('up{job="medmlops"}') and float(query('up{job="medmlops"}')[0]['value'][1]) == 1)
    alerts = wait_for(lambda: [a for a in httpx.get(prom + '/api/v1/alerts').json()['data']['alerts']
                              if a['labels']['alertname'] == 'SyntheticDriftDetected' and a['state'] == 'firing'])
    graf = httpx.Client(base_url='http://127.0.0.1:3000', auth=('admin', os.environ['GRAFANA_PASSWORD']))
    datasource = graf.get('/api/datasources/uid/medmlops-prometheus/health')
    datasource.raise_for_status()
    assert datasource.json()['status'] == 'OK'
    dashboard = graf.get('/api/dashboards/uid/medmlops-v2')
    dashboard.raise_for_status()
    assert len(dashboard.json()['dashboard']['panels']) == 9
    for _ in range(15):
        httpx.post(api + '/predict', headers=headers, json=body).raise_for_status()
    wait_for(lambda: query('medmlops_requests_total{route="/predict",status="200"}'))
    quantiles = {str(q): query(f'histogram_quantile({q}, sum by(le)(medmlops_request_seconds_bucket))')
                 for q in (0.5, 0.95, 0.99)}
    rollback = verified_switch(first, actor, ROOT / 'deploy', api, token, rollback=True)
    assert gov.active()['version'] == str(first)

    # A failed HTTP verification must restore the previous approved pointer.
    try:
        verified_switch(second, actor, ROOT / 'deploy', 'http://127.0.0.1:1', token)
    except httpx.HTTPError:
        pass
    else:
        raise AssertionError('Failed verification was accepted')
    assert gov.active()['version'] == str(first)
    gov.reconcile()
    assert httpx.get(api + '/ready', headers=headers).json()['version'] == str(first)
    client = MlflowClient(tracking_uri())
    assert client.get_model_version_by_alias(MODEL_NAME, 'champion').version == str(first)
    # Real tracking outage blocks publication; no fallback registry or deployment.
    uri_before = os.environ.get('MLFLOW_TRACKING_URI')
    os.environ['MLFLOW_TRACKING_URI'] = 'http://127.0.0.1:1'
    try:
        try:
            publish(ROOT, actor, experiment='unreachable-test')
        except Exception:
            pass
        else:
            raise AssertionError('Unavailable tracking accepted publication')
    finally:
        if uri_before is None:
            os.environ.pop('MLFLOW_TRACKING_URI')
        else:
            os.environ['MLFLOW_TRACKING_URI'] = uri_before
    assert gov.active()['version'] == str(first)
    subprocess.run(['docker', 'compose', 'exec', '-T', 'api', 'python', '-m', 'scripts.cache_probe',
                    'corrupt', '--version', str(first)], check=True, capture_output=True)
    try:
        assert httpx.get(api + '/ready', headers=headers).status_code == 503
        assert httpx.post(api + '/predict', headers=headers, json=body).status_code == 503
    finally:
        subprocess.run(['docker', 'compose', 'exec', '-T', 'api', 'python', '-m', 'scripts.cache_probe',
                        'restore', '--version', str(first)], check=True, capture_output=True)
    assert httpx.get(api + '/ready', headers=headers).status_code == 200

    # Stop and recreate containers, retaining named volumes. No volume removal.
    before_count = len(gov.history())
    for name, args in (('down', ['down']), ('up', ['up', '-d', '--wait', '--wait-timeout', '240'])):
        completed = subprocess.run(['docker', 'compose', *args], capture_output=True, text=True)
        log = completed.stdout + completed.stderr
        for key in ('POSTGRES_PASSWORD', 'MLFLOW_DB_PASSWORD', 'GOVERNANCE_DB_PASSWORD', 'MEDMLOPS_API_TOKEN', 'GRAFANA_PASSWORD'):
            log = log.replace(os.environ[key], '[REDACTED]')
        (EVIDENCE / f'compose-{name}.txt').write_text(log)
        assert completed.returncode == 0
    assert gov.active()['version'] == str(first)
    assert len(gov.history()) >= before_count
    assert httpx.get(api + '/ready', headers=headers, timeout=30).json()['version'] == str(first)
    assert client.get_run(tracking['versions'][tracking['selected']]['run_id']).info.status == 'FINISHED'
    fetch(first, ROOT / 'restart-download')
    assert graf.get('/api/dashboards/uid/medmlops-v2').status_code == 200
    assert all(Path(r['evidently']['html']).exists() for r in (stable, shifted, degraded))
    history = gov.history()
    assert not any(token in json.dumps(e) or 'patient_name' in json.dumps(e) for e in history)
    result = {'passed': True, 'first_deploy': first_deploy, 'second_deploy': second_deploy,
              'bad_candidate_rejected': bad_version, 'http_parity_error': abs(response.json()['probabilities'][0] - expected),
              'stable_alerts': stable['alerts'], 'shifted_alerts': shifted['alerts'],
              'degraded_alerts': degraded['alerts'], 'prometheus_scrape': scrape,
              'firing_alerts': alerts, 'latency_quantiles': quantiles,
              'grafana_datasource': datasource.json(), 'dashboard_panels': 9,
              'rollback': rollback, 'compensation': True, 'concurrent_audit': True,
              'append_only_audit': True, 'recreated_container_persistence': True,
              'serving_role_cannot_deploy': True, 'stale_switch_rejected': True,
              'tracking_outage_blocks_publication': True, 'corruption_blocks_http_readiness': True,
              'mlflow_run_and_artifact_persistence': True, 'audit_events': len(history),
              'reports': [r['evidently'] for r in (stable, shifted, degraded)], 'clinical_validity': False}
    (EVIDENCE / 'end-to-end.json').write_text(json.dumps(result, indent=2))
    (EVIDENCE / 'audit-events.json').write_text(json.dumps(history, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
