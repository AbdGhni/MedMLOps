"""Bootstrap the restricted API role, then apply owned application schema."""
import os

import psycopg
from psycopg import sql

from medmlops.governance import Governance
from medmlops.settings import load_local


def main():
    load_local()
    host = os.getenv('POSTGRES_HOST', '127.0.0.1')
    port = os.getenv('POSTGRES_PORT', '5433')
    with psycopg.connect(host=host, port=port, dbname='postgres', user='postgres',
                         password=os.environ['POSTGRES_PASSWORD']) as conn:
        if not conn.execute("SELECT 1 FROM pg_roles WHERE rolname='serving'").fetchone():
            conn.execute(sql.SQL('CREATE ROLE serving LOGIN PASSWORD {}').format(sql.Literal(os.environ['SERVING_DB_PASSWORD'])))
    Governance().migrate()
    print('Target schema and restricted serving role ready')


if __name__ == '__main__':
    main()
