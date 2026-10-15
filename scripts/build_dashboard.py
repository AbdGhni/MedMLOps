"""Generate a provisioned dashboard with concrete PromQL queries."""
import json
from pathlib import Path


def main():
    expressions = [
        ('Request throughput', 'sum(rate(medmlops_requests_total[1m]))'),
        ('Error ratio', 'sum(rate(medmlops_requests_total{status=~"5.."}[1m])) / clamp_min(sum(rate(medmlops_requests_total[1m])), 0.001)'),
        ('Latency p50', 'histogram_quantile(0.50, sum by (le) (rate(medmlops_request_seconds_bucket[1m])))'),
        ('Latency p95', 'histogram_quantile(0.95, sum by (le) (rate(medmlops_request_seconds_bucket[1m])))'),
        ('Latency p99', 'histogram_quantile(0.99, sum by (le) (rate(medmlops_request_seconds_bucket[1m])))'),
        ('Approved served version', 'medmlops_model_info'),
        ('Lifecycle and rollback audit', 'medmlops_lifecycle_events'),
        ('Drift incidents', 'medmlops_drift_alert'),
        ('Governance availability', 'medmlops_audit_available'),
    ]
    panels = [{'id': i + 1, 'title': title, 'type': 'timeseries',
               'datasource': {'type': 'prometheus', 'uid': 'medmlops-prometheus'},
               'targets': [{'refId': 'A', 'expr': expression}],
               'gridPos': {'x': i % 3 * 8, 'y': i // 3 * 8, 'w': 8, 'h': 8}}
              for i, (title, expression) in enumerate(expressions)]
    dashboard = {'uid': 'medmlops-v2', 'title': 'MedMLOps synthetic platform',
                 'schemaVersion': 41, 'version': 1, 'refresh': '5s',
                 'time': {'from': 'now-15m', 'to': 'now'}, 'panels': panels}
    path = Path('infrastructure/grafana/dashboards/medmlops.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dashboard, indent=2))


if __name__ == '__main__':
    main()
