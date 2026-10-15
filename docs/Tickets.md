# MedMLOps delivery backlog

## Phase 5

Final audit, fixes, RC version, independent clone installation and recruiter
documentation: see `validation/phase5/FINAL_REPORT.md` for executed results.
Open release items: upstream vulnerabilities, authentic visual captures,
authorized GitHub publication/remote CI and protected environment configuration.
The Phase 4 table below is historical and retains its original acceptance boundary.

## Phase 4 execution — 2026-10-14

### Current authoritative status

| Tickets | Status / acceptance boundary |
|---|---|
| MM-002 | Hash lock and clean Linux install verified; global security gate remains open (unpatched transitive advisories) |
| MM-003/005/010 | Core plus target test/lint checks verified; original functionality preserved |
| MM-004 | Real DVC scheduling/cache/reproduction/seed/checkout verified |
| MM-006/007/008/009/013 | Actual MLflow/PG/FastAPI lifecycle, approval, least-privilege serving, concurrency, corruption, restart and rollback verified |
| MM-011 | Actual Evidently reports and persisted drift/performance incidents verified |
| MM-012 | Prometheus scrape/rule/quantiles and Grafana APIs verified; rendered-panel capture blocked by absent browser surface |
| MM-014 | Workflows implemented; local equivalents executed; remote CI/reviewer configuration and security release remain open |
| MM-015 | Local end-to-end demo and English portfolio docs delivered; visual capture and publication remain open |

See `validation/phase4/status.md`, `quality.json`, `tracking.json`, `dvc.json`,
`end-to-end.json` and `audit-events.json` for executed evidence. No push performed.
Historical Phase 3 status text below is retained as acceptance/history, not current
service status. A complete unrestricted release is not claimed while these gates remain open.

Reference: `[private-revision]`, workspace `C:/Projects/MedMLOps`.
Network and Docker work through authorized elevation. PostgreSQL 16.13 is running
with persistent storage. Target dependencies installed in `.venv`; `pip check`
passes. A complete 211-distribution SHA256 lock is generated from PyPI metadata.
The initial 22 tests plus four FastAPI failure-contract tests pass (26 total).
MLflow/PG adapters are implemented; actual tracking/registry verification is next.
Security audit found fixable pip/Flask issues (updated), plus unpatched transitive
DiskCache/NLTK advisories; final scan and risk assessment remain required.
Historical blocked statuses below describe Phase 3, superseded only by recorded
Phase 4 evidence, not by code presence.

- MM-004: **LOCAL VERIFIED**: genuine DVC repro, no-op, forced hash parity,
  changed seed invalidation, cache push and older-lock checkout all passed.
  See `validation/phase4/dvc.json` and command logs. A discovered NumPy 2
  scalar-comparison forest boundary bug was fixed and regression-tested.
- MM-008/011/012: implemented; live service acceptance remains pending.

Latest recovery update: MM-000 re-audited; MM-002 and genuine service tickets remain blocked by managed network/ACL/engine restrictions. Archive and history backup verified; migration syntax reviewed, execution pending authorized user context. Independent MM-007 artifact/metric verification added with three tests (22 total passing), but promotion, identity-backed audit and Model Registry remain incomplete. See `validation/phase3-status.md` for exact evidence and required intervention.

Status vocabulary: **DONE** means every mandatory check was executed successfully; **LOCAL VERIFIED** means functional offline checks passed but a target quality/integration prerequisite remains open; **BLOCKED** names an unavailable prerequisite; **TODO** means not implemented. Creation of a file never completes an integration.

For every ticket: inspect Git status before editing, preserve unrelated files, implement in dependency order, run listed mandatory tests, capture actual commands and exit codes, update this backlog, and create a coherent local commit. Definition of done (DoD) includes those steps plus the ticket-specific acceptance below. Push requires explicit user permission. No automatic promotion or deletion.

## MM-000 — Environment audit — DONE
- Description/objective: establish what can really run before claiming delivery.
- Prerequisites/dependencies: existing MedMLOps checkout; none.
- Files: `docs/validation/environment.json`, ADR 0002, `docs/Progress.md`.
- Steps: inspect cwd/Git/instructions; inventory interpreter/packages/CLI; query Docker and unprivileged resources; record failures.
- Mandatory checks/acceptance: actual versions and errors recorded, no credentials printed, no other project modified. DoD: audit evidence persisted. RAM query denied is an audit finding, not invented capacity.

## MM-001 — Scope and architecture — DONE
- Description/objective: map business failures to target components and acceptance scenarios.
- Prerequisites/dependencies: MM-000.
- Files: `docs/adr/0001*`, `0003*`, `docs/architecture/*`, `docs/validation/acceptance.md`, this backlog.
- Steps: separate MVP/extensions; specify trust boundaries; draw seven diagrams; define component contracts and end-to-end evidence.
- Mandatory checks/acceptance: all seven diagram types and 18 components documented; no legacy store counted as MLflow; no compliance claims. DoD: design recorded; diagram rendering remains portfolio verification in MM-015.

## MM-002 — Isolated bootstrap and dependency lock — BLOCKED
- Description/objective: make a fresh installation reproducible and auditable.
- Prerequisites/dependencies: MM-000; PyPI access.
- Files: `pyproject.toml`, `requirements-target.in`, final transitive lock, package layout, quality configuration.
- Steps: resolve compatible maintained versions; install clean venv; migrate to `src/` with installation tests; configure pytest/Ruff/Mypy/pip-audit; record resolver output.
- Mandatory tests/acceptance: clean `pip check`, pytest, Ruff, appropriate typing checks and dependency scan; complete verified lock. DoD: no unresolved dependency compatibility claims.

## MM-003 — Synthetic v2 data and schema — LOCAL VERIFIED
- Description/objective: traceable, shareable data covering demographics, biology, physiology and fictitious history.
- Prerequisites/dependencies: MM-000; final target checks depend on MM-002.
- Files: `medmlops/datasets.py`, `configs/params.json`, `tests/test_v2.py`, data contract documentation.
- Steps: seed generator; strict Pydantic input; snapshot hashes; quality gates; immutable read verification.
- Mandatory tests/acceptance: identical seed identical CSV; changed seed new hash; reject unknown/missing/nonfinite/bool/outlier/duplicate/bad labels; corrupt snapshots refused. DoD: local tests pass, then target pytest/Ruff checks pass.

## MM-004 — DVC five-stage pipeline — BLOCKED (definition present)
- Description/objective: reproduce datasets and pipeline outputs from a commit.
- Prerequisites/dependencies: MM-002, MM-003; DVC installation and cache storage.
- Files: `dvc.yaml`, `.dvc/config`, `dvc.lock`, stage modules and PowerShell scripts.
- Steps: initialize actual DVC repository; configure local persistent remote/cache; run generate/validate/prepare/train/evaluate; commit small metadata only.
- Mandatory tests/acceptance: successful `dvc repro`, second no-op, forced reproduction parity, changed parameter invalidation, checkout of older dataset. DoD: genuine DVC outputs and logs; direct Python stages do not complete this ticket.

## MM-005 — LR/RF training and evaluation — LOCAL VERIFIED
- Description/objective: compare models reproducibly and avoid test-set selection.
- Prerequisites/dependencies: MM-003; final quality depends MM-002; DVC integration MM-004.
- Files: `experiments.py`, `scoring.py`, `pipeline.py`, `tests/test_v2.py`.
- Steps: disjoint 60/20/20 split; five-fold CV on train; LR/RF fit; validation threshold and model selection; test metrics and calibration; JSON artifact parity; provenance.
- Mandatory tests/acceptance: subject disjointness, both models, CV counts, AUC/PR-AUC/F1/sensitivity/specificity/Brier/confusion/calibration, parity ≤1e-12, dataset/hash/commit/params/run-id/dependency metadata. DoD: verified clean-commit reproduction plus target quality checks.

## MM-006 — Persistent MLflow Tracking and Registry — BLOCKED
- Description/objective: centralized comparable experiments and preserved model versions.
- Prerequisites/dependencies: MM-002, MM-005, Docker engine; PostgreSQL.
- Files: tracking adapter, registry adapter, Compose services, integration tests.
- Steps: real PostgreSQL backend and artifact volume; log params/metrics/models/data/commit; registry versions; candidate and champion aliases; compare real runs.
- Mandatory tests/acceptance: two real UI/API runs, registered artifacts, restart persistence, alias/version history and failed tracking behavior. DoD: no local JSON evidence counted as MLflow integration.

## MM-007 — Approval and promotion gate — LOCAL METRIC GATE ONLY
- Description/objective: prevent publication of deficient candidates and attribute decisions.
- Prerequisites/dependencies: MM-005, MM-006 and target audit storage.
- Files: offline `experiments.gate`; governance/controller modules and target tests pending.
- Steps: verify artifact integrity + metrics; reject deficient candidate; explicit actor approval; audit actor/time/version/checks; candidate→approved→champion.
- Mandatory tests/acceptance: random/bad candidate blocked, missing actor rejected, transactional audit, no training-only promotion. DoD: actual registry and audit transitions tested; offline metric rejection alone is partial.

## MM-008 — FastAPI serving — BLOCKED
- Description/objective: safely expose only the deployed approved version.
- Prerequisites/dependencies: MM-002, MM-006, MM-007.
- Files: target serving app/schemas, deployment loader, unit/integration HTTP tests.
- Steps: `/health`, `/ready`, `/model/info`, `/predict`, `/metrics`; strict schemas; correlation ID; auth; controlled pinned load; structured safe logs and latency.
- Mandatory tests/acceptance: real Uvicorn requests; 401/422/413/503; matching approved/served version; corruption denial; no feature/token exposure. DoD: real FastAPI execution, not legacy Flask.

## MM-009 — PostgreSQL audit and incidents — BLOCKED
- Description/objective: consolidate technical evidence and operational decisions.
- Prerequisites/dependencies: MM-002, real PostgreSQL; feeds MM-007/008/013.
- Files: migrations, governance repository, audit/incident tests.
- Steps: append-only app events with actor/time/correlation/model/dataset/checks; incidents and alerts; retention policy; backup instructions.
- Mandatory tests/acceptance: transactional pointer/event, concurrent writes, least privilege, failure behavior, persistence after restart. DoD: genuine PostgreSQL tests and evidence.

## MM-010 — Window monitoring mathematics — LOCAL VERIFIED
- Description/objective: distinguish data, prediction and measured labelled degradation.
- Prerequisites/dependencies: MM-003, MM-005; target quality MM-002.
- Files: `monitor_windows.py`, test suite, scenario script.
- Steps: reference/current windows; PSI and corrected KS; minimum samples; optional reliable labels; observed AUC change; synthetic shift and inverted-label incident.
- Mandatory tests/acceptance: stable window no alert in reproducible fixture; shifted data/predictions alert; no-label performance unavailable; small window inconclusive; misaligned labels refused; degraded labels alert; no automatic retrain/promotion. DoD: local tests plus target quality checks. Fixture results do not establish statistical false-positive guarantees.

## MM-011 — Evidently integration and reports — BLOCKED
- Description/objective: persist inspectable drift reports using the requested engine.
- Prerequisites/dependencies: MM-002, MM-010; actual Evidently installation.
- Files: Evidently adapter, HTML/JSON reports and integration tests.
- Steps: verified version/API; reference/current schema; data and prediction reports; attach metadata; small-window policy.
- Mandatory tests/acceptance: real Report execution, saved readable HTML and JSON, restart-accessible reports, alerts associated with incidents. DoD: no custom PSI report counted as Evidently.

## MM-012 — Prometheus/Grafana observability — BLOCKED
- Description/objective: provision useful operational and lifecycle panels automatically.
- Prerequisites/dependencies: MM-008, MM-009, Docker, exporter dependency.
- Files: exporter, `infrastructure/prometheus/*`, `infrastructure/grafana/*`, dashboard JSON, Compose.
- Steps: counters/histograms/version/quality/pipeline failures/promotions/rollbacks; scrape config; provision datasource and dashboard; p50/p95/p99 and error rate panels.
- Mandatory tests/acceptance: real scrape, PromQL responses, Grafana datasource health and dashboard API after clean start, no manual setup. DoD: rendered panels and execution evidence.

## MM-013 — Controlled deploy and rollback — BLOCKED
- Description/objective: restore a previous approved version after an incident.
- Prerequisites/dependencies: MM-006/007/008/009.
- Files: deployment and rollback controllers, runbook, real end-to-end tests.
- Steps: identify incident/active version; choose previous approval; atomic pointer+audit; verify ready/prediction/version; compensate on failure; reconcile aliases.
- Mandatory tests/acceptance: rejected model never served; successful rollback confirmed by actual HTTP; failure compensation and actor audit. DoD: real target service drill, not v1 rollback test.

## MM-014 — CI, explicit CT and controlled CD — BLOCKED
- Description/objective: automate verification and delivery without implicit promotion.
- Prerequisites/dependencies: MM-002/004/006/008/012/013; Docker, dependency access.
- Files: separate Actions workflows and PowerShell/Makefile commands.
- Steps: CI lint/tests/audit/build/schema/artifact/non-regression; manual CT; approval-controlled local CD; capture failure evidence.
- Mandatory tests/acceptance: successful local equivalents and real container smoke; negative cases block downstream; CI execution once publication authorized. DoD: real runs, not YAML presence.

## MM-015 — End-to-end and portfolio delivery — BLOCKED
- Description/objective: an interviewer can clone, launch and inspect the full lifecycle.
- Prerequisites/dependencies: all target integrations; GitHub push authorization separately required.
- Files: English README, Windows guide, demo, diagrams, captures, CV/LinkedIn text, final evidence.
- Steps: automate all 18 acceptance steps; clean clone launch; dashboard screenshots; limitations; publish only if authorized.
- Mandatory tests/acceptance: all success criteria in `docs/validation/acceptance.md`, no exposed secrets, docs match runtime, preserved evidence. DoD: no open required service integration and authorized publication.

## MM-016 — Regulatory boundary documentation — DOCUMENTED
- Description/objective: prevent clinical or certification misrepresentation.
- Prerequisites/dependencies: MM-001; official source verification.
- Files: `docs/validation/regulatory-boundary.md`, README, model/data docs.
- Steps: identify relevant references and actual MVP limitations; state no medical recommendations; record synthetic-only restriction.
- Mandatory review/acceptance: sources link official publishers; no certification/conformity claim; no real health data. DoD: source-supported review recorded, not legal qualification of a product.
