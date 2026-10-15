# Final technical audit

Scope: repository Python modules, tests, scripts, pipeline/configuration, Compose,
Dockerfile, workflow definitions, documentation, tracked/history inventory and
installed dependency source relevant to the advisories. Static review is backed
by actual tests and service probes; it is not a penetration test or certification.

| Concern | Finding / correction | Verification |
|---|---|---|
| Architecture | v1 Flask/SQLite reference and v2 integrations are separate; PG pointer is authoritative, MLflow alias is eventually reconciled | Unit/reference tests and real registry/HTTP lifecycle |
| Data contracts | Strict bounds, finite numbers, forbidden identifiers/unknown fields, immutable content-addressed snapshots | Adversarial schema tests and pipeline validation |
| Leakage / selection | Disjoint subject partitions, train-only scaling/CV; validation threshold and winner selection | Partition/parity tests and clean-clone pipeline |
| Reproduction | DVC stages/cache/local remote, forced numeric hash parity, seed invalidation and restoration | `execution/dvc.json` and DVC logs |
| Integration | Actual MLflow/PG/Uvicorn/Evidently/Prometheus/Grafana APIs, no integration mocks substituted | `execution/end-to-end.json` and `tracking.json` |
| Auth error handling | Non-ASCII bearer caused TypeError in string comparison; corrected to byte comparison | New 401 regression; OpenAPI HTTP bearer scheme tested |
| CLI/version inputs | Registry version was also a local directory component; numeric validation now precedes network/cache use | Traversal/absolute-path/punctuation rejection regression |
| Documentation UX | Swagger previously lacked an auth scheme/Authorize control definition | OpenAPI security schema regression and documented capture procedure |
| Persistence | Named volumes retained across down/up; source and historical evidence retained | Live recreated-container assertions and independent local clone |
| Approval/deployment | Explicit operator policy, approved digest, transactional pointer/audit/outbox; verification and generation-guarded compensation | Rejected candidate, stale switch, rollback, outage and integrity fault drills |
| Secrets | Random local credentials, ignore/Docker exclusions, parameterized SQL; expanded ignore rules | Scoped current/history scan with no secret values emitted |
| CI | Fixed missing redirect directory; added scoped typing; separate ignored evidence paths | Local equivalent commands passed; remote execution pending |
| CD | Blocking dependency audit before approval; explicit Bash, timeout, serialized deployment | YAML/static review; hosted environment/reviewer enforcement pending |
| Versioning | pyproject and module version aligned to 2.0.0rc1 | Package wheel built and installed in fresh clone |
| Docs/evidence | Recruiter README, seven portfolio files, current status pointers and explicit historical boundaries | Link checks and final evidence manifest |

## Test scope and limits

Pytest and unittest exercise the same 30 tests; their counts must not be added
together as 60 independent tests. Pytest also reports 29 subtests. The live E2E
is a separate script with real integrations. Ruff passes across medmlops/scripts/tests;
Mypy checks six selected target modules with untyped function bodies checked,
not strict typing of every legacy module. Starlette emits one httpx deprecation
warning. Replacing that client is a future compatibility update, not a hidden failure.

Historical scripts `http_smoke.py` and `benchmark.py` target v1 routes; they are
not v2 acceptance commands or new performance evidence. Tests cover those v1
API/CLI behaviors; the active target HTTP lane is `validate_phase4.py`. Observed
Prometheus quantiles are histogram estimates during fault drills, not production
SLAs or load-test benchmarks.

## Remaining engineering boundaries

Approval evidence is consistent/recomputed at publication, but the registry and
operator are trusted; there is no independent signed verifier. The audit is
append-only for normal application operations, not protected against owners or
TRUNCATE. Actor strings are not enterprise identity. No off-host restore, load
capacity, distributed rate limiting, cloud deployment, notification routing,
browser rendering, remote Actions execution or clinical validation was established.
See SECURITY_REVIEW and LICENSE_REVIEW before any publication decision.
