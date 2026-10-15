# Phase 5 final report

Date: 2026-10-15. Release candidate: **2.0.0rc1**, local tag `v2.0.0-rc.1`.
Functional local acceptance passed. Security release clearance, remote Actions
execution and authentic rendered screenshots remain incomplete. No push or remote
repository creation was performed. Synthetic data only; no clinical validation.

## Completed and verified

| Lane | Executed result | Evidence |
|---|---|---|
| Pytest | 30 passed, 29 subtests; one Starlette/httpx deprecation warning | `execution/final-quality/tests.txt` |
| unittest | 30 tests, OK; same suite, not 30 additional independent tests | `execution/unittest.log` |
| Lint / typing / consistency | Ruff passed; Mypy passed on six target modules with checked untyped bodies; pip check passed | `execution/final-quality/quality.json` and text logs |
| Five-stage pipeline | Synthetic generation, validation, preparation, both fits and quality gate passed from clean source | `execution/pipeline.log`; `execution/execution.json` |
| DVC | Repro/no-op/force, identical numeric model hashes, seed invalidation and older output checkout passed | `execution/dvc.json`, `execution/dvc-*.txt` |
| MLflow / PostgreSQL | Real runs/versions, candidate artifacts, explicit approval, missing-actor rejection, pyfunc parity and DVC hash consistency | `execution/tracking.json` |
| Compose | Build/start and service health passed; E2E down/up retained named volumes | `execution/compose-build-start.log`, `compose-down.txt`, `compose-up.txt`, `final-compose.log` |
| API / artifact safety | Authenticated real HTTP predictions, exact numeric parity, schema rejection, body limit, corrupt-cache 503 and recovery | `execution/end-to-end.json`; `final-smoke.json` |
| Lifecycle | Deficient version 11 rejected; approved RF version 9 deployed; rollback restored LR version 10; failed verification compensated | `execution/end-to-end.json`, `audit-events.json` |
| Governance | Concurrent audit, append-only application audit, restricted serving role, stale deployment rejection, registry outage failure | `execution/end-to-end.json` |
| Monitoring | Stable window had no alerts; shifted heart rate/oxygen and predictions alerted; inverted labels triggered performance loss; actual Evidently HTML/JSON persisted | `execution/end-to-end.json`, host `runtime/phase4/reports/` |
| Prometheus / Grafana | Actual scrape, SyntheticDriftDetected firing, histogram queries, healthy datasource and nine provisioned dashboard panels | `execution/end-to-end.json`; no browser-rendering claim |
| Fresh local clone | Independent clone, new venv, hash-locked install, project wheel build/install, pip check, 30 tests and pipeline passed; model hashes match host | `clean-clone.json`, `clean-clone-package-install.txt` |
| Final endpoints | API health, Swagger, MLflow health, Grafana health and Prometheus readiness all returned 200; model info confirmed LR version 10; bearer scheme present | `final-smoke.json` |
| Secret / history inventory | No known local credential or selected key/token pattern found in scanned current files/reachable history | `release-inventory.json` — scope limits apply |

The complete scripted functional acceptance ran on clean commit
`[private-revision]`. Commit
`[private-revision]` then aligned the module version with
the package RC and retained the refreshed DVC lock. Final pytest/lint/type/pip
checks, the independent clone package installation/pipeline and final image
build/endpoint checks cover that source. Subsequent changes are documentation,
inventories and retained evidence. Model mathematics did not change between these
commits. The tag identifies the final documentation/evidence snapshot.

Initial functional audit found 27 tests passing. Three added tests cover non-ASCII
bearer rejection, registry version/path rejection and Swagger bearer declaration.
Other fixes include CI output-directory creation, static typing, an explicit CD
security gate, workflow shell/timeouts/concurrency and separate evidence paths.
See [technical audit](TECHNICAL_AUDIT.md) for the implementation review.

## Reproduction and installation evidence

The clone under ignored `runtime/phase5-clean-clone` uses an independent `.git`
directory and new `.venv`; no developer venv was copied. Package installation
built `medmlops-2.0.0rc1-py3-none-any.whl`, and the clean pipeline reports
`git_dirty=false`. Same-platform model hashes match the main checkout. Linux
image builds reused validated dependency layers; Phase 5 does not claim a new
cache-free Linux installation. Phase 4's fresh locked Linux install evidence is
preserved. Python host version is 3.12.4; cross-platform byte identity is not claimed.

The normal sandbox blocked pip temporary-file access; the prescribed escalation
resolved installation. Docker initially was stopped, then started through the
authorized mechanism. No ACL, proxy, host security policy or patient-data source
was changed. All work stayed under the requested project directory, apart from
standard tool-managed caches and temporary files used by authorized tools.

## Security remains a failing gate

Both the updated Windows audit and actual Linux API-image audit report **three
raw findings in two packages, representing two distinct vulnerabilities**:

- DiskCache 5.6.3: PYSEC-2026-2447 / CVE-2025-69872, repeated twice in the raw response. DVC → dvc-data → DiskCache; writable poisoned cache can result in code execution.
- NLTK 3.10.3: PYSEC-2026-3740 / CVE-2026-81726. Evidently → NLTK; affected model persistence APIs bypass path roots. Those NLP model-path operations are not used by this tabular application.

Current PyPI metadata and advisory responses supply no compatible fixed version.
The risk is constrained by local trusted-operator operation, not eliminated.
No advisory is ignored and CD's audit runs before approval. The complete release
validator intentionally returns exit **1** because the audit fails after all
functional lanes passed. See [security analysis](SECURITY_REVIEW.md),
`execution/dependency-audit.json` and `execution/linux-dependency-audit.json`.

Other limits: shared local token and asserted actor identity; trusted registry;
no independent signed evidence, TLS gateway, enterprise IAM, load/HA guarantee,
off-host restore verification or notification routing. Database owners are not
contained by application audit triggers. See [limitations](../../portfolio/LIMITATIONS.md).

## GitHub and portfolio readiness

**GitHub:** source, local coherent commits, RC version, README and workflows are
prepared for review. They are **not an unconditionally cleared publication or
production release**. Root Git has no remote configured. No remote Actions run,
protected branch/environment setting or runner registration was performed.
Publication needs explicit destination/visibility approval and a push; the audit
would currently prevent green target CI/CD. See [GitHub checklist](GITHUB_READINESS.md).

**Portfolio:** all seven requested English files are delivered in `docs/portfolio/`,
including a 5–10 minute script, 30 grounded technical questions and five conservative
CV bullets. README contains problem, architecture, stack, workflow, quickstart,
results, testing, monitoring/rollback, security boundaries and roadmap. These are
usable for an interview with the disclosed limitations.

**Visual demonstration:** computer-use inventory returned no authorized app/browser
surface. Actual UI rendering and screenshots remain unverified; none was invented.
URLs, authentic capture checklist and report paths are in DEMO_SCRIPT.md. API-level
Grafana validation does not substitute for rendered panels.

**Licensing:** pre-existing MIT LICENSE preserved unchanged. No new license was
added. Confirm this existing choice before publication. Dependency metadata,
installed license-file checks and redistribution caveats are in LICENSE_REVIEW.md;
no full container legal/SBOM clearance is claimed.

## Actions requiring the owner

1. Confirm the destination repository and visibility, then explicitly authorize any creation/push and remote workflow execution. Nothing remote is performed by this delivery.
2. Confirm the existing MIT license choice; no automatic relicensing will occur.
3. Configure remote protections, reviewers and isolated trusted runner before manual CT/CD, if remote publication is authorized. Never expose the loopback services publicly.
4. Provide an authorized browser surface or take authentic screenshots using the manual checklist.
5. Resolve upstream advisories before claiming a green security release. Do not disable the gates; there is currently no demonstrated compatible upstream fix.

## Exact local demonstration commands

Existing installed checkout, PowerShell, from `C:/Projects/MedMLOps`:

```powershell
.venv/Scripts/python.exe -m scripts.bootstrap_local
# A clean git status is required before training approved candidates.
.venv/Scripts/python.exe -m medmlops.pipeline all --work runtime/phase4
docker compose up --build -d --wait --wait-timeout 240
$env:MEDMLOPS_EVIDENCE_DIR = 'runtime/demo-evidence'
.venv/Scripts/python.exe -m scripts.check_tracking
.venv/Scripts/python.exe -m scripts.validate_phase4
.venv/Scripts/python.exe -m medmlops.lifecycle history
```

MLflow: http://127.0.0.1:5000 · Swagger: http://127.0.0.1:8000/docs ·
Grafana: http://127.0.0.1:3000/d/medmlops-v2 · Prometheus: http://127.0.0.1:9090/alerts.
Grafana uses admin and the generated local `.env` password. Swagger Authorize
accepts the local API token; keep credentials out of captures. The full scenario
deliberately injects faults and recreates containers without removing volumes.
For first installation and a timed demonstration see [DEMO_SCRIPT](../../portfolio/DEMO_SCRIPT.md).

For complete repeat release validation from clean source:
`.venv/Scripts/python.exe -m scripts.validate_release`. Exit 1 is expected while
the current audit findings remain; inspect each lane instead of calling it green.
