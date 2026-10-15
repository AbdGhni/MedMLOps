# Local platform runbook

Run from a committed repository with Python 3.12 and Docker Desktop Linux engine.
Use only synthetic data. Bindings are loopback-only: 5000 MLflow, 8000 API,
9090 Prometheus, 3000 Grafana and 5433 PostgreSQL.

## Bootstrap and verification (PowerShell)

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install --index-url https://pypi.org/simple pip==26.2.1
.venv/Scripts/python.exe -m pip install --index-url https://pypi.org/simple --require-hashes -r requirements-target.lock
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
.venv/Scripts/python.exe -m ruff check medmlops scripts tests
.venv/Scripts/python.exe -m scripts.bootstrap_local
# Train before producing modified tracked evidence: provenance must be clean.
.venv/Scripts/python.exe -m medmlops.pipeline all --work runtime/phase4
docker compose up --build -d --wait --wait-timeout 240
$env:MEDMLOPS_EVIDENCE_DIR = 'runtime/demo-evidence'
.venv/Scripts/python.exe -m scripts.check_tracking
.venv/Scripts/python.exe -m scripts.validate_phase4
.venv/Scripts/python.exe -m scripts.check_dvc
```

On Linux use `python3` and `.venv/bin/python`. Set `MEDMLOPS_EVIDENCE_DIR=runtime/demo-evidence`
on Linux to preserve historical evidence. For a complete clean-source release
recheck, run `python -m scripts.validate_release`; it records separate logs under
`runtime/phase5-execution` and returns nonzero when the dependency audit fails.
The DVC checker prepends the
venv executable directory to PATH so stage commands use the locked environment.
It disables analytics and puts DVC's system/global/site configuration caches
inside `runtime`. A local DVC remote is a reproducibility demonstration, not an
off-machine backup. Keep `.dvc/config`, `dvc.yaml` and `dvc.lock` in Git; cohort,
prepared arrays, model outputs and caches stay out of Git. `dvc checkout` restores
the outputs described by a previous committed lock; then `dvc repro` checks them.

Managed sessions must authorize PyPI/Docker/Git writes through their escalation
mechanism. Do not bypass the session proxy, alter ACLs or disable security tools.
Some Windows sandbox temporary-directory ACLs still reject Python temporary
files. Tracking uses explicit workspace staging instead of MLflow `log_dict`
temporary directories; tests use `-p no:cacheprovider`. If a subprocess is denied,
request the normal authorization rather than changing system permissions.

## Inspect and operate

`.env` contains generated local-only credentials and is ignored by Git and Docker.
Grafana's user is `admin`; read its password locally from `.env`. API requests use
`Authorization: Bearer <MEDMLOPS_API_TOKEN>`. `/health` is process liveness;
`/ready` verifies PostgreSQL approval, pinned artifact hash and v2 schema.
`/model/info`, `/predict`, `/metrics` and `/docs` expose the implemented interfaces.
The metrics endpoint is internal to this local demo and scraped by Prometheus.

```powershell
.venv/Scripts/python.exe -m medmlops.lifecycle history
.venv/Scripts/python.exe -m medmlops.lifecycle approve --version VERSION --actor local-operator
.venv/Scripts/python.exe -m medmlops.lifecycle deploy --version VERSION --actor local-operator
.venv/Scripts/python.exe -m medmlops.lifecycle rollback --version PREVIOUS_APPROVED_VERSION --actor local-operator
.venv/Scripts/python.exe -m medmlops.lifecycle reconcile
docker compose ps
docker compose stop
docker compose start
```

Passing training does not approve. Operator policy in `configs/params.json` and
verified held-out evidence govern approval. The API's `serving` database role can
read approvals/deployment/events and insert aggregate audit records, but cannot
change the deployment pointer, approvals or existing events. Operator actor names
are local assertions; enterprise identity/RBAC is an extension, not a demo claim.

Deployment locks the pointer row, commits pointer/audit/outbox together, verifies
actual readiness and prediction, then reconciles the champion alias. A failed
verification compensates to the previous version, guarded by generation to avoid
overwriting a concurrent deployment. An alias failure leaves a retryable outbox;
the PostgreSQL pointer remains the deployment authority.

## Incidents and persistence

The full validation command deliberately registers a rejected constant model,
injects synthetic drift and reversed labels, deploys an independently approved
challenger, rolls back, exercises failed verification and temporarily corrupts
the serving cache. It restores cache bytes and ends on the approved LR version.
It also runs `docker compose down` and `up` without removing volumes. Do not run
fault injection against a shared service while other users rely on it.

PostgreSQL, MLflow artifacts, serving cache, Prometheus and Grafana use named
volumes. `volume-init` sets only the two application mount root ownerships for
UID 10001; serving and MLflow then run without root. `migrate` initializes the
restricted API database role and application tables. Do not delete volumes to
fix a deployment fault. Keep approved models indefinitely; no automated purge is
implemented. Back up PostgreSQL via `pg_dump`, MLflow's artifact volume and the
ignored host reports; test restores before relying on a backup.

Evidently HTML/JSON and mathematical reports live in `runtime/phase4/reports`.
The Prometheus rule `SyntheticDriftDetected` fires on the latest evaluated window's
alert count. Incidents persist in PostgreSQL; notification delivery to people is
not configured. Drift never trains or promotes automatically.

## CI and release boundary

Target CI checks lock installation, tests, lint, real Compose lifecycle, DVC and
the dependency audit. Manual CT publishes candidates only. Manual CD requires a
`medmlops-local` self-hosted runner, repository secrets and required reviewers for
the `local-demo` GitHub environment. These workflows have not executed on GitHub;
publication requires separate authorization. The security job intentionally fails
while the documented unpatched transitive advisories remain. Local functional
acceptance is not a production security release or clinical validation.
