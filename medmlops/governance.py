"""PostgreSQL approval, atomic deployment/audit, and retryable alias outbox."""
import re
import uuid
from pathlib import Path

import psycopg
from mlflow import MlflowClient
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from .experiments import gate
from .settings import database_uri, tracking_uri
from .tracking import MODEL_NAME, fetch

SCHEMA = """
CREATE TABLE IF NOT EXISTS approvals (
 version text PRIMARY KEY, model_sha256 text NOT NULL, dataset text NOT NULL,
 actor text NOT NULL, evidence jsonb NOT NULL, created_at timestamptz DEFAULT now());
CREATE TABLE IF NOT EXISTS deployment (
 id integer PRIMARY KEY CHECK(id=1), version text REFERENCES approvals(version), generation bigint NOT NULL DEFAULT 0);
INSERT INTO deployment(id) VALUES(1) ON CONFLICT DO NOTHING;
CREATE TABLE IF NOT EXISTS events (
 id bigserial PRIMARY KEY, created_at timestamptz DEFAULT now(), actor text NOT NULL,
 action text NOT NULL, version text, correlation text NOT NULL, details jsonb NOT NULL);
CREATE TABLE IF NOT EXISTS outbox (
 id bigserial PRIMARY KEY, version text NOT NULL, completed boolean NOT NULL DEFAULT false);
CREATE OR REPLACE FUNCTION forbid_event_mutation() RETURNS trigger AS $$
BEGIN RAISE EXCEPTION 'append-only audit'; END; $$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS immutable_events ON events;
CREATE TRIGGER immutable_events BEFORE UPDATE OR DELETE ON events FOR EACH ROW EXECUTE FUNCTION forbid_event_mutation();
GRANT SELECT ON approvals,deployment,events TO serving;
GRANT INSERT ON events TO serving;
GRANT USAGE ON SEQUENCE events_id_seq TO serving;
"""


def actor_id(actor):
    if not isinstance(actor, str) or not re.fullmatch(r'[A-Za-z0-9._@:-]{1,128}', actor):
        raise ValueError('Explicit actor required')
    return actor


class Governance:
    def __init__(self, uri=None):
        self.uri = uri or database_uri()

    def connect(self):
        return psycopg.connect(self.uri, row_factory=dict_row, connect_timeout=5)

    def migrate(self):
        with self.connect() as conn:
            conn.execute(SCHEMA)

    def event(self, actor, action, version=None, details=None, correlation=None, conn=None):
        actor_id(actor)
        args = (actor, action, version, correlation or uuid.uuid4().hex, Jsonb(details or {}))
        sql = 'INSERT INTO events(actor,action,version,correlation,details) VALUES(%s,%s,%s,%s,%s)'
        if conn is not None:
            conn.execute(sql, args)
        else:
            with self.connect() as connection:
                connection.execute(sql, args)

    def approve(self, version, actor, cache):
        actor_id(actor)
        files, digest, _ = fetch(version, cache)
        report, evidence = (files[k] for k in ('report.json', 'verification.json'))
        # The operator-controlled policy is authoritative, not thresholds uploaded by a candidate.
        import json
        config = json.loads(Path('configs/params.json').read_text())
        if report['model_sha256'] != digest or files['model.json']['dataset_version'] != report['dataset_version']:
            raise ValueError('Approval provenance mismatch')
        if evidence['dataset_version'] != report['dataset_version'] or evidence['recomputed_test'] != report['test']:
            raise ValueError('Verified evaluation mismatch')
        comparison = {'selected': report['kind'], 'models': {report['kind']: report}}
        decision = gate(comparison, config)['selected_passed']
        if not decision or not all(evidence['checks'].values()) or evidence['model_sha256'] != digest:
            self.event(actor, 'approval_rejected', str(version), {'quality_passed': decision})
            raise ValueError('Candidate gate or verified evidence failed')
        with self.connect() as conn:
            conn.execute('INSERT INTO approvals(version,model_sha256,dataset,actor,evidence) VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING',
                         (str(version), digest, report['dataset_version'], actor, Jsonb(evidence)))
            self.event(actor, 'approved', str(version), evidence['checks'], conn=conn)
        MlflowClient(tracking_uri()).set_model_version_tag(MODEL_NAME, str(version), 'lifecycle', 'approved')
        return {'version': str(version), 'model_sha256': digest}

    def active(self):
        with self.connect() as conn:
            return conn.execute('SELECT d.version,d.generation,a.model_sha256,a.dataset FROM deployment d LEFT JOIN approvals a ON a.version=d.version WHERE d.id=1').fetchone()

    def switch(self, version, actor, action='deploy', expected_generation=None):
        actor_id(actor)
        with self.connect() as conn:
            current = conn.execute('SELECT version,generation FROM deployment WHERE id=1 FOR UPDATE').fetchone()
            if expected_generation is not None and current['generation'] != expected_generation:
                raise ValueError('Concurrent deployment changed; refusing stale switch')
            if not conn.execute('SELECT 1 FROM approvals WHERE version=%s', (str(version),)).fetchone():
                raise ValueError('Only approved versions can be deployed')
            conn.execute('UPDATE deployment SET version=%s,generation=generation+1 WHERE id=1', (str(version),))
            self.event(actor, action, str(version), {'previous': current['version']}, conn=conn)
            conn.execute('INSERT INTO outbox(version) VALUES(%s)', (str(version),))
        return current

    def reconcile(self):
        # Serialize with deployment writers. Replay current pointer, never a stale alias event.
        with self.connect() as conn:
            current = conn.execute('SELECT version FROM deployment WHERE id=1 FOR UPDATE').fetchone()
            pending = conn.execute('SELECT id FROM outbox WHERE NOT completed').fetchall()
            if pending and current['version']:
                MlflowClient(tracking_uri()).set_registered_model_alias(MODEL_NAME, 'champion', current['version'])
                conn.execute('UPDATE outbox SET completed=true WHERE NOT completed')
        return len(pending)

    def history(self):
        with self.connect() as conn:
            return conn.execute('SELECT id,actor,action,version,correlation,details FROM events ORDER BY id').fetchall()

    def observability(self):
        with self.connect() as conn:
            counts = conn.execute('SELECT action,count(*) AS count FROM events GROUP BY action').fetchall()
            latest = conn.execute("SELECT details FROM events WHERE action='monitoring' ORDER BY id DESC LIMIT 1").fetchone()
        return counts, latest['details']['alert_count'] if latest else 0


def verified_switch(version, actor, cache, api_url, token, rollback=False):
    import httpx
    gov = Governance()
    files, digest, _ = fetch(version, Path(cache) / str(version))
    with gov.connect() as conn:
        approval = conn.execute('SELECT model_sha256 FROM approvals WHERE version=%s', (str(version),)).fetchone()
    if not approval or digest != approval['model_sha256']:
        raise ValueError('Approval integrity mismatch')
    previous = gov.switch(version, actor, 'rollback' if rollback else 'deploy')
    try:
        headers = {'Authorization': f'Bearer {token}'}
        ready = httpx.get(f'{api_url}/ready', headers=headers, timeout=30)
        ready.raise_for_status()
        if ready.json()['version'] != str(version):
            raise ValueError('Served version mismatch')
        from .datasets import FEATURES, generate
        record = generate(500).iloc[0][list(FEATURES)].to_dict()
        for key in ('sex_code', 'prior_event'):
            record[key] = int(record[key])
        prediction = httpx.post(f'{api_url}/predict', headers=headers, json={'records': [record]}, timeout=30)
        prediction.raise_for_status()
        if prediction.json()['version'] != str(version):
            raise ValueError('Prediction version mismatch')
    except Exception:
        if previous['version']:
            gov.switch(previous['version'], actor, 'compensation', previous['generation'] + 1)
        else:
            with gov.connect() as conn:
                changed = conn.execute('UPDATE deployment SET version=NULL,generation=generation+1 WHERE id=1 AND generation=%s RETURNING id',
                                       (previous['generation'] + 1,)).fetchone()
                if changed:
                    gov.event(actor, 'compensation', details={'previous': None}, conn=conn)
        gov.event(actor, 'deployment_incident', str(version))
        raise
    gov.reconcile()
    gov.event(actor, 'deployment_verified', str(version))
    return {'version': str(version), 'previous': previous['version'], 'verified': True}
