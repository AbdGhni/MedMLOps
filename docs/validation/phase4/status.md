# Phase 4 delivery status — 2026-10-14

Reference checkout: `[private-revision]`; work stayed in `C:/Projects/MedMLOps`.
The full local service lifecycle passed. No GitHub commit was pushed.

| Phase | Executed result | Evidence |
|---|---|---|
| 4.1 MLflow | PostgreSQL backend, persistent artifact proxy, real LR/RF runs/versions, numeric pyfunc parity, controlled approval | `tracking.json`, `end-to-end.json` |
| 4.2 DVC | Five stages, local remote/cache, repro/no-op/force, seed invalidation, previous dataset checkout; MLflow model hashes match DVC | `dvc.json`, `dvc-*.txt`, `tracking.json` |
| 4.3 FastAPI | Real Uvicorn HTTP; strict v2 schemas, bearer auth, privacy-preserving validation/audit, approved pinned model, corrupt-cache 503 | `tests.txt`, `end-to-end.json` |
| 4.4 Compose | Fresh hashed Linux install, healthchecks, loopback ports, persistent volumes, non-root application processes, restricted API DB role; down/up persistence | `compose-up.txt`, `compose-down.txt`, `end-to-end.json` |
| 4.5 Monitoring | Actual Evidently HTML/JSON; stable window, data/prediction shift and labelled degradation; real scrape and firing Prometheus rule; Grafana datasource/dashboard APIs | `end-to-end.json`; host reports under `runtime/phase4/reports` |
| 4.6 CI/CD | Target CI, manual CT and reviewer-controlled local CD definitions; local test/lint/type/build/integration equivalents executed | `.github/workflows`, `quality.json` |
| 4.7 End-to-end | Deficient model rejected, separately approved challenger deployed, drift incident, verified rollback and failure compensation; durable audit/run/artifact history | `end-to-end.json`, `audit-events.json` |

27 tests pass (the original 22, four API contract tests and one forest boundary
regression). The live integration scenario is an additional executed lane, not a
mock. Pip consistency, Ruff and Mypy with `--check-untyped-defs` pass. Scoped typing
does not claim that every legacy module has strict complete annotations.

The fresh locked Linux image runs Python 3.12.15 and `pip check` reports no broken
requirements. Its Python base digest is pinned in the Dockerfile; the host venv
uses Python 3.12.4. No cross-platform numeric byte-identity claim is made.

Final demonstrated registry state: LR version 7 is served, RF version 6 is the
separately approved challenger, constant version 8 is rejected. Actual run IDs are
in `tracking.json`. Training provenance is clean commit
`[private-revision]`; these artifacts' source hashes match
the verified DVC outputs. The original fixture's test AUC is .86698 LR/.83770 RF;
actual HTTP probability parity error is zero for the demonstrated request.

## Remaining release restrictions

- The real security audit still reports three advisories in DiskCache/NLTK, with
  no fixed versions returned. `dependency-audit.json` and `security.md` retain
  them. CI's security gate is not bypassed. This is a local synthetic demo, not a
  cleared production release.
- GitHub Actions have not executed remotely; reviewer requirements and a local
  self-hosted runner must be configured before manual CD. No push is authorized.
- Computer-use inventory returned no browser/app surfaces; actual rendered
  Grafana panels and screenshots could not be inspected. Provisioning, panel
  definitions, data source health, queries, scrape and alert APIs did execute.
  Restore an approved browser surface to complete the visual portfolio check.
- Operator actor names and the shared prediction token are suitable for a local
  single-operator exercise, not enterprise user identity. MLflow is accessible
  only on loopback and trusts local operator processes.

Python temporary-directory ACLs in the sandbox still affect some libraries.
Workspace staging and cache-free test execution avoid unnecessary temporary
files; Git/Docker/PyPI operations used their authorized escalation mechanisms.
No system security policy, proxy or host ACL was changed.

Historical Phase 3 blockers and evidence remain in their original documents for
traceability. They do not describe the current working service stack.
