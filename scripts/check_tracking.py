"""Executed MLflow/PG integration lane, with retained redacted evidence."""
import json
import os
import uuid
from pathlib import Path

from mlflow import MlflowClient, pyfunc

from medmlops.governance import Governance
from medmlops.settings import tracking_uri
from medmlops.tracking import MODEL_NAME, fetch, publish


def main():
    root = Path('runtime/phase4')
    tracking = publish(root, 'local-demo-operator', experiment='phase4-' + uuid.uuid4().hex[:8])
    gov = Governance()
    gov.migrate()
    selected = tracking['versions'][tracking['selected']]['version']
    approval = gov.approve(selected, 'local-demo-operator', root / 'download')
    missing_actor_rejected = False
    try:
        gov.approve(selected, '', root / 'download')
    except ValueError:
        missing_actor_rejected = True
    assert missing_actor_rejected
    files, digest, _ = fetch(selected, root / 'download')
    assert digest == approval['model_sha256']
    client = MlflowClient(tracking_uri())
    import numpy as np

    from medmlops.datasets import FEATURES, generate
    from medmlops.scoring import predict
    for item in tracking['versions'].values():
        run = client.get_run(item['run_id'])
        assert run.info.status == 'FINISHED' and run.data.params and run.data.metrics
        assert client.get_model_version(MODEL_NAME, item['version']).run_id == item['run_id']
        folder = root / 'pyfunc' / item['version']
        folder.mkdir(parents=True, exist_ok=True)
        client.download_artifacts(item['run_id'], 'bundle/MLmodel', str(folder))
        client.download_artifacts(item['run_id'], 'bundle/model.json', str(folder))
        loaded = pyfunc.load_model(str(folder))
        frame = generate(500)[list(FEATURES)]
        numeric = json.loads((folder / 'model.json').read_text())
        assert np.max(np.abs(loaded.predict(frame) - predict(numeric, frame.to_numpy(dtype=float)))) <= 1e-12
    if Path('data/comparison.json').exists():
        dvc = json.loads(Path('data/comparison.json').read_text())
        assert {k: r['model_sha256'] for k, r in dvc['models'].items()} == {
            k: r['model_sha256'] for k, r in tracking['versions'].items()}
    assert any(e['action'] == 'approved' for e in gov.history())
    result = {'tracking': tracking, 'approval': approval, 'missing_actor_rejected': True,
              'artifact_integrity': True, 'postgres_audit': True,
              'pyfunc_numeric_parity': True, 'dvc_model_hash_consistency': Path('data/comparison.json').exists(),
              'promotion_performed': False}
    target = Path(os.getenv('MEDMLOPS_EVIDENCE_DIR', 'docs/validation/phase4'))
    target.mkdir(parents=True, exist_ok=True)
    (target / 'tracking.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
