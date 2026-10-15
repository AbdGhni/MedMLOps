# End-to-end acceptance contract

All checks must execute against actual target technologies. A direct Python step can verify its calculations but cannot verify DVC scheduling, MLflow persistence, FastAPI serving or a Grafana panel.

Phase 4 authoritative execution: see `phase4/end-to-end.json`, `tracking.json`,
`dvc.json` and `quality.json`. Steps 1–11 and 13–18 ran against actual technologies,
including HTTP restoration, immutable/concurrent PG audit and recreated-container
persistence. Step 12 has datasource/dashboard/query API evidence; rendered-panel
inspection is unavailable because the computer-use inventory has no browser
surfaces. The security release gate still reports unpatched transitive advisories,
and remote Actions/publication are not authorized. The state column below is the
historical pre-integration checkpoint, preserved for traceability.

| Step | Required observable evidence | Current state |
|---|---|---|
| 1 Generate synthetic cohort | repeated seed gives identical snapshot | local tested |
| 2 Validate data | strict schema and negative cases | local tested |
| 3 Version dataset | `dvc repro`, lock/cache, older checkout | blocked: DVC |
| 4 Train LR and RF | both fitted, five-fold train CV | local tested |
| 5 Compare candidates | validation selection, held-out metrics | local tested |
| 6 Track MLflow | real run IDs/UI, params/data/commit/artifacts | blocked |
| 7 Validate candidate | integrity and metric gate rejects deficient version | metric portion tested; full gate pending |
| 8 Controlled promotion | actor approval and lifecycle audit | pending target registry |
| 9 Approved model load | actual deployment pointer != alias-only state | pending FastAPI/PG |
| 10 Predict | real authenticated HTTP and served version | legacy HTTP only; target pending |
| 11 Collect metrics | real Prometheus scrape with counters/histograms | blocked |
| 12 Visualize | automatically provisioned Grafana panels and queries | blocked |
| 13 Inject reproducible shift | fixed-seed current window | local tested |
| 14 Alert | data/prediction report plus stored incident, Evidently HTML | math tested; persistence/Evidently pending |
| 15 Simulate regression | reject bad candidate; separately incident on approved deployment | metric rejection and labelled change tested; service drill pending |
| 16 Rollback | previous approved pointer switched transactionally | legacy only; target pending |
| 17 Confirm restoration | ready, real prediction and actual version | target pending |
| 18 Audit review | actor/time/model/dataset/checks/correlation history | target PG pending |

Additional release requirements: compatible dependency lock, pytest/Ruff and security scan; clean installation; persistent Compose volumes; API schemas; artifact hash verification; metrics p50/p95/p99 and error rates; no automatic training-based promotion; no secrets in Git; complete documentation; all required scenarios passing. No ticket is DONE merely because code exists.

Reproduction tolerance: same source commit, dataset version, configuration and verified dependency environment must give identical numeric JSON hashes on the tested platform. Record cross-platform numeric differences rather than claiming architecture-independent byte identity. Uncommitted sources are tagged `git_dirty=true` and are never presented as reproduction from the recorded commit alone.
