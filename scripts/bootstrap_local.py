"""Create ignored local demo credentials once; never print secret values."""
import secrets
from pathlib import Path


def main():
    path = Path('.env')
    existing = path.read_text() if path.exists() else ''
    present = {line.split('=', 1)[0] for line in existing.splitlines() if '=' in line}
    values = {key: secrets.token_hex(24) for key in (
        'POSTGRES_PASSWORD', 'MLFLOW_DB_PASSWORD', 'GOVERNANCE_DB_PASSWORD',
        'SERVING_DB_PASSWORD', 'MEDMLOPS_API_TOKEN', 'GRAFANA_PASSWORD') if key not in present}
    path.write_text(existing + ''.join(f'{k}={v}\n' for k, v in values.items()), encoding='utf-8')
    print('Local demo credentials ready in ignored .env; existing values preserved')


if __name__ == '__main__':
    main()
