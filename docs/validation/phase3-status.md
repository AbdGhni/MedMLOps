# Phase 3 status and compliance matrix

This is an interim report, not final end-to-end acceptance. No package installation, real target-service integration, durable migration or GitHub push succeeded or was claimed in this phase.

| Requested step | Actual result | Evidence / next dependency |
|---|---|---|
| 1 Windows diagnosis | Executed: exact repository/base commit; archive; ACLs; DNS; configured proxy; pip flags/config; package/venv inventory; Docker | `phase3-diagnostic.json`, `runbooks/environment-unblock.md`; firewall/TLS status unavailable, not inferred |
| 2 Durable migration and backup | Archive verified; complete-history Git bundle created and verified; original retained. Migration blocked by sandbox ACLs | `runtime/MedMLOps-v2-backup.bundle`; migration script syntax valid, not executed |
| 3 MLflow | Not installed, not integrated | Approved package access and real PostgreSQL/Docker needed |
| 4 DVC | Definition retained; no real DVC reproduction | DVC installation needed |
| 5 FastAPI | Existing Pydantic contract retained; target app integration blocked | FastAPI/Uvicorn installation; no Flask substitution |
| 6 Docker | CLI/Compose present; engine unavailable; Desktop helper log writes denied | User starts Desktop from an authorized context |
| 7 Monitoring | Existing core mathematics retained and retested; no real Evidently/Prometheus/Grafana | Dependencies and engine required |
| 8 CI/CD | Existing definitions retained; no real Actions execution | Target dependencies and eventual explicitly authorized publication |
| 9 Full end-to-end | Not executed; remains blocked | All required genuine services |
| 10 Delivery docs | Exact Windows recovery guide, interim matrix and diagnostic evidence added | Final professional release depends on end-to-end acceptance |

## Independent security work completed

`medmlops/candidate_validation.py` validates actual v2 numeric artifacts: finite dimensions, positive LR scaling, bounded valid forest trees, no cycles, strict model/schema hash, prepared-data integrity and subject separation. It recomputes AUC, PR-AUC, AP, sensitivity, specificity, F1, Brier and confusion on the saved held-out data, and compares them with the recorded report. An explicit actor identifier is required; control characters and absent identity are rejected. Dirty training provenance is ineligible in the CLI gate.

The command `python -m medmlops.candidate_validation --work runtime/clean-commit-repro --actor local-operator` passes on the actual previously trained clean candidate. Both `approval_performed` and `promotion_performed` remain false. This is validation evidence, not a Model Registry or audit-database integration.

## Executed checks

- Initial unchanged v2 baseline: all 19 tests pass.
- After adding three security tests: all 22 tests pass; original 19 preserved.
- `python -m scripts.validate_v2`: pipeline plus 22-test suite and synthetic monitoring scenarios pass; `full_platform_passed=false` remains explicit.
- Diagnostic HTTPS request fails with WinError 10061 through configured `127.0.0.1:9`; DNS succeeds. No TLS, proxy, ACL or firewall protection is bypassed.
- `git bundle create` and `git bundle verify` succeed and confirm complete history through the v2 baseline.
- PowerShell parser reports no syntax errors for the migration script. An initial nested-shell parser invocation failed because of variable expansion; corrected direct invocation passes. No migration execution is claimed.
- Compilation and whitespace checks pass; they do not replace Ruff, Mypy or pip-audit.

## Immediate user intervention

Run the migration script from an authorized normal PowerShell, verify its output, reopen the durable copy as the writable workspace, and verify HTTPS/package access plus Docker server availability. Exact commands and expected results are in `docs/runbooks/environment-unblock.md`. Do not send credentials and do not delete the temporary original. The agent can resume installation and genuine integration only when these dependencies are available.
