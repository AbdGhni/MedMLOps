"""Evidently reports plus labelled v2 mathematics and persistent incidents."""
import json
import uuid
from pathlib import Path

from evidently import Report
from evidently.presets import DataDriftPreset

from .datasets import FEATURES
from .monitor_windows import monitor
from .scoring import predict


def inspect_window(bundle, reference, current, policy, root, governance, actor, version, labels=None, reference_metrics=None):
    result = monitor(bundle, reference, current, policy, labels, reference_metrics)
    if result['status'] == 'inconclusive':
        return result
    folder = Path(root) / uuid.uuid4().hex
    folder.mkdir(parents=True)
    frames = []
    for frame in (reference, current):
        numeric = frame[list(FEATURES)].copy()
        numeric['prediction'] = predict(bundle, numeric.to_numpy(dtype=float))
        frames.append(numeric)
    snapshot = Report([DataDriftPreset(method='psi', threshold=policy['psi_threshold'])],
                      metadata={'version': str(version), 'schema': bundle['schema']}).run(
                          current_data=frames[1], reference_data=frames[0])
    snapshot.save_html(str(folder / 'evidently.html'))
    (folder / 'evidently.json').write_text(snapshot.json())
    result['evidently'] = {'executed': True, 'html': str(folder / 'evidently.html'),
                          'json': str(folder / 'evidently.json')}
    (folder / 'monitoring.json').write_text(json.dumps(result, indent=2))
    # Aggregate event only. Raw synthetic feature windows stay out of operational logs.
    details = {'status': result['status'], 'alert_count': len(result['alerts']),
               'alerts': result['alerts'], 'report': folder.name}
    governance.event(actor, 'monitoring', str(version), details)
    if result['alerts']:
        governance.event(actor, 'drift_incident', str(version), details)
    return result
