"""Local/container configuration. Credentials are never included in evidence."""
import os
from pathlib import Path


def load_local():
    if Path('.env').exists():
        for line in Path('.env').read_text().splitlines():
            if line and not line.startswith('#'):
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)


def database_uri():
    load_local()
    role = os.getenv('MEDMLOPS_DB_ROLE', 'governance')
    if role not in ('governance', 'serving'):
        raise ValueError('Unsupported application role')
    password = os.environ['SERVING_DB_PASSWORD' if role == 'serving' else 'GOVERNANCE_DB_PASSWORD']
    host = os.getenv('POSTGRES_HOST', '127.0.0.1')
    port = os.getenv('POSTGRES_PORT', '5433')
    return f'postgresql://{role}:{password}@{host}:{port}/governance'


def tracking_uri():
    return os.getenv('MLFLOW_TRACKING_URI', 'http://127.0.0.1:5000')
