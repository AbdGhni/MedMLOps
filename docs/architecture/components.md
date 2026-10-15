# Component contracts

Phase 4 now implements and executes the target components described here.
Current code entry points are `tracking.py`, `governance.py`, `serving.py`,
`monitoring.py`, `lifecycle.py`, `scripts/check_dvc.py` and
`scripts/validate_phase4.py`; actual evidence is in `../validation/phase4`.
The verification cells below record the earlier design checkpoint. Use the
Phase 4 status for current execution and remaining release restrictions.

The interfaces below are target contracts. “Pending” denotes required but unexecuted integration. Shared configuration is `configs/params.json` and environment variables from `.env.example`. All generated outputs are synthetic and outside Git; small execution reports are retained as evidence.

| Component / responsibility | Input → output / interface | Dependencies / configuration | Errors and recovery | Verification |
|---|---|---|---|---|
| Generator: independent fictitious subjects | seed, n → immutable CSV + SHA manifest; `pipeline generate` | NumPy/Pandas; dataset config | invalid n or corruption; fail, regenerate new snapshot | determinism, bounds and changed seed tested |
| Validation: contract and quality | snapshot → report; `pipeline validate` | Pydantic + dataset schema | missing, unknown, duplicate, nonfinite, bad labels; block downstream | adversarial contract tests pass |
| Dataset versioning | snapshot and code → DVC metadata/cache | DVC pending; `dvc.yaml` | missing cache or remote; restore exact version or fail | `dvc repro` pending |
| Features: split and train-only transformations | validated data → disjoint NPZ; `pipeline prepare` | sklearn; split seed | subject overlap; reject and rebuild | overlap and coverage tests pass |
| Training | partitions + config → LR/RF JSON artifacts | sklearn; seed, CV, forest bounds | fit/parity failure; stop, retain prior approved version | both candidates + five folds tested |
| Tracking | commit/data/params/metrics → runs in MLflow | MLflow/PostgreSQL pending | tracking unavailable; fail publication, retain local evidence | real server test pending |
| Evaluation | validation/test probabilities → metrics/calibration | sklearn; validation selection | insufficient labels/classes; fail explicitly | metrics and selection tests pass |
| Registry | accepted run → candidate/approved/champion versions | MLflow pending; model name | invalid artifact/version; no alias update | real registry test pending |
| Approval gate | metrics, hash, actor → decision and audit | threshold config; PostgreSQL pending | failed checks or missing identity; reject | offline metric rejection tested; actor integration pending |
| Serving | strict features → versioned predictions | FastAPI/Uvicorn pending; API token, deployment pointer | malformed 422; absent/corrupt 503 | Pydantic tested; target HTTP pending |
| Prediction logging | request metadata → aggregate structured event | correlation ID, model hash; PG pending | persistence fault; fail or explicit degraded state | no tokens/features in event test pending |
| Monitoring engine | reference/window/optional labels → report | NumPy/SciPy/sklearn; minimum window | small sample; inconclusive, no performance claim | independent tests scheduled MM-010 |
| Drift detector | features/probabilities → PSI/KS and Evidently | Evidently pending; thresholds | incompatible schemas; reject; preserve evidence | math tests scheduled, real Evidently pending |
| Alerting | threshold failures → incident events | retention config, actor; PG pending | delivery failure; persist incident and retry | incident integration pending |
| Rollback controller | incident + prior approval → served previous version | PG pointer + MLflow outbox pending | readiness failure; compensating switch and escalation | legacy rollback tested; target drill pending |
| Audit trail | lifecycle event → actor/time/version/checks | PostgreSQL pending; append-only app permissions | database unavailable; block mutation | transaction and identity tests pending |
| CI/CD/CT | commit/manual workflow → builds, runs, verified deploy | Actions/Docker/PyPI pending | failed checks; block downstream; no training-only promotion | legacy workflow unexecuted; target lanes pending |
| Dashboard | operational/lifecycle metrics → panels | Prometheus/Grafana pending; provisioned files | empty scrape/unavailable exporter; visibly degraded | automatic provisioning + actual queries pending |

The legacy SQLite audit and Flask UI remain a reference only. They cannot satisfy pending target integration tests in this matrix.
