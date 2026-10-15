#!/bin/sh
set -eu
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  --set=mlpass="$MLFLOW_DB_PASSWORD" --set=govpass="$GOVERNANCE_DB_PASSWORD" <<'SQL'
CREATE ROLE mlflow LOGIN PASSWORD :'mlpass';
CREATE DATABASE mlflow OWNER mlflow;
CREATE ROLE governance LOGIN PASSWORD :'govpass';
CREATE DATABASE governance OWNER governance;
SQL
