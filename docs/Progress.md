# Phase log — expanded specification, 2026-10-14

## Phase 5 — release candidate, 2026-10-15

Current verification and publication boundaries are in
`validation/phase5/FINAL_REPORT.md`. Portfolio documents are in `portfolio/`.
Historical Phase 4 evidence below is preserved, including its then-current model
version numbers. Current deployed versions must be read from Phase 5 evidence.
No remote publication is authorized.

## Phase 4 — execution in durable workspace

### Final local execution

All service phases ran: MLflow 3.17.1/PostgreSQL tracking and registry, DVC 3.67.1
reproduction, FastAPI/Uvicorn serving, Evidently 0.7.23 reports, Prometheus 3.15.0
scrape/firing alerts, Grafana 13.2.2 datasource/dashboard APIs, Compose recreation
and verified rollback/compensation. 27 tests, Ruff, scoped checked-body Mypy and
pip consistency pass. End-to-end evidence is `validation/phase4/end-to-end.json`.
LR version 7 is served after rollback, version 6 is the approved RF challenger,
version 8 is deliberately deficient and denied. HTTP parity error is zero.
CI/manual CT/controlled CD are implemented but have not run on GitHub. No push.
Remaining release gates: unpatched DiskCache/NLTK advisories and rendered Grafana
capture (computer-use inventory has no browser/app surfaces). README and operator
runbook describe the executed stack and exact limits. Subsequent paragraphs record
intermediate progress and historical phases.

Workspace: `C:/Projects/MedMLOps`; reference commit `[private-revision]`.
Authorized network/Docker access confirmed. PostgreSQL 16.13 started, healthcheck
passed. Installed MLflow 3.17.1, DVC 3.67.1, Evidently 0.7.23, FastAPI 0.143.1,
Uvicorn 0.54.0 and target tooling in isolated `.venv`. `pip check` passes.
26 tests pass before service integration. PyPI-based hash lock generated.
Tracking and transactional governance adapters implemented; real execution is
pending image build. Initial audit reported vulnerabilities; pip and Flask were
updated, remaining unpatched transitive advisories require explicit documentation.
No GitHub push performed. Earlier entries below are historical evidence.

DVC five-stage execution passed: first repro, no-op, force reproduction with
identical dataset/model hashes, seed 43 invalidation, and original lock checkout.
The changed-seed lane exposed a forest boundary bug (NumPy float32 comparison
rounded double thresholds); explicit Python float comparison fixes sklearn parity.
A focused regression test was added. Evidently adapter, FastAPI exporter and
Prometheus/Grafana provisioning are written; live checks follow image startup.

## Latest: environment recovery phase

See `validation/phase3-status.md` and `runbooks/environment-unblock.md`. The v2 base `[private-revision]` was verified before modifications; all 19 baseline tests passed. Three artifact-security tests were added and all 22 pass. No target-service or durable-migration success is claimed. A complete-history backup bundle exists; normal user-context migration/network/Docker actions are required. The original and its v2 archive remain intact. Earlier phase entries below are historical snapshots.

Repository: `C:/home/USER/AppData/Local/Temp/MedMLOps`. `C:/home/USER is not a Git repository. The existing MedMLOps checkout is used; no other project is modified. Prior commit `[private-revision]` is the v1 prototype, not the requested target stack.

Each row gives objective/atomic tasks, files/deliverable, prerequisites, mandatory checks/acceptance, risk and real status. Ticket-specific details and DoD are in `Tickets.md`.

| Phase | Objective / atomic tasks | Files and deliverable | Dependencies | Checks / acceptance | Risk / real status |
|---|---|---|---|---|---|
| 0 Audit | inspect Git, instructions, tools, Docker, resources | environment evidence, ADR 0002 | none | versions/errors captured without secrets | completed; Docker engine and privileged RAM query unavailable |
| 1 Scope | define MVP/extensions, ADRs, 7 diagrams, 18 contracts, backlog | architecture, ADRs, acceptance, Tickets | 0 | required design documents present | completed design; rendering verification later |
| 2 Bootstrap | resolve/install/lock; pytest/Ruff/audit; package migration | target requirements, final lock pending | 0 + PyPI | clean install/pip check/quality | blocked; target stack not frozen |
| 3 Synthetic data | generate/schema/quality/hash snapshots | datasets.py, params, v2 tests | installed core; final 2 | seed/hash/contract negative cases | local verified; not final quality complete |
| 4 Training | prepare splits; LR/RF CV; validation selection; test metrics | experiments/scoring/pipeline | 3 | disjoint subjects, metric suite, inference parity | local verified; DVC scheduling pending |
| 5 Tracking | start PG/MLflow; log/register/compare | adapters + services pending | 2, 4, Docker | actual server and persistence tests | blocked |
| 6 Validation | gate + identity approval + lifecycle | offline metric gate; target governance pending | 4, 5, PG | deficient candidates blocked; actor audit | partial; metric rejection tested |
| 7 Serving | FastAPI routes/schema/loader/correlation/auth | Pydantic data schema exists; app pending | 2, 5, 6 | real Uvicorn smoke, errors, pinned model | blocked; Flask v1 not counted |
| 8 Monitoring | windows/labels/shift; Evidently + Prom/Graf | monitor_windows.py; service configs pending | 4; services require 2,7,Docker | shift/no-label/small-window; real reports/panels | math locally verified; integrations blocked |
| 9 CI/CD | separate CI/manual CT/controlled CD | legacy workflow + core-ci definition; full target pending | 2,5,7,8 | lint/tests/audit/build/deploy checks | local core command tested; workflows unexecuted; target blocked |
| 10 Governance | actor audit/incidents/atomic rollback/retention | lifecycle ADR, runbook design | 5,6,7,PG | real atomic pointer/audit and compensation | blocked target implementation |
| 11 E2E | run all 18 acceptance steps | acceptance checklist, evidence | required integrations | genuine full lifecycle | blocked; no mocked completion |
| 12 Portfolio | English README, Windows guide, demo, captures, summary | documentation in progress | 11 for final | clean clone launch and real dashboards | partial; not a complete portfolio release |

## Commands actually executed

- `git rev-parse --show-toplevel` at cwd: fails, not a repository.
- `git status --short`, `git log -1 --oneline`, `rg --files` in MedMLOps: existing clean v1 identified.
- `python --version`: 3.12.4; metadata inventory confirms installed core/Pydantic versions.
- `docker version`, `docker info`: client exists; engine named pipe unavailable.
- `docker compose version`: 5.6.0; `git --version`: 2.55.0.windows.5.
- `Get-CimInstance Win32_ComputerSystem`: access denied. Unprivileged Python resource query succeeds.
- `python -m pip index versions fastapi --index-url https://pypi.org/simple --timeout 5 --retries 0`: fails; repeated after disabling inherited `PIP_NO_INDEX=1` also fails. No target versions resolved.
- `python -m unittest discover -s tests -v`: 19 tests pass (12 legacy + 7 v2), zero failed in last direct execution.
- `python -m medmlops.pipeline all`: generation, validation, preparation, both model fits, comparison and offline gate execute successfully. No MLflow publication or deployment performed.
- `python -m scripts.audit_environment`: actual inventory persisted to `validation/environment.json`.
- `python -m scripts.validate_v2`: full local core verification passes; evidence in `validation/evidence-v2`; summary explicitly sets `full_platform_passed=false`.
- `python -m compileall -q medmlops scripts tests` and `git diff --check`: pass. These do not replace Ruff, Mypy or a dependency audit.
- Clean-source reproduction at commit `[private-revision]`: successful five-stage run with `git_dirty=false`; identical dataset and both model hashes. See `validation/evidence-v2/clean-reproduction.json`. Same audited platform only; not a DVC or clean-install claim.
- CI definitions are separated: legacy checks only `test_platform.py`; `core-ci.yml` runs the real locally tested core command. Neither workflow has run on GitHub in this session.
- Clean local clone attempts (`git clone --no-hardlinks . runtime/checkout-verification` and explicit `--local` with absolute source) fail inside Git's child shell: `couldn't create signal pipe, Win32 error 5`. No cloned-checkout validation was executed. This is an additional environment restriction, not a GitHub authentication result. The successful clean working-tree reproduction must not be described as a clean clone or clean installation.

## Verified v2 results

Seed 42, 4,000 subjects, 800 held-out test observations. Logistic Regression: test AUC 0.86698, train CV mean AUC 0.89248, F1 0.64088. Random Forest: test AUC 0.83770, train CV mean AUC 0.86947, F1 0.60808. Logistic Regression is selected on **validation** AUC, not these test results. Both demonstration gates pass; no registry promotion or deployment takes place. Numeric export parity errors are 1.11e-16 (LR) and 0 (RF). These are synthetic results, not clinical evidence.

## Next action and limitations

Restore package index access and start Docker, then MM-002. Continue independent checks and documentation meanwhile. No GitHub push without user permission. The environment still restricts durable directory creation; this checkout remains temporary. The old archive is a v1 snapshot and must not be mistaken for the expanded target release.

The current core snapshot is exported separately as `MedMLOps-v2-core.zip`. It excludes `.git`, runtime data/models and virtual environments. It is not the complete target release. Training provenance requires a committed repository; archive recipients should work in an initialized, committed checkout. The original local Git history is retained in the existing repository.
