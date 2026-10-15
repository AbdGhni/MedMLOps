# Architecture decisions and tradeoffs

| Decision | Reason grounded in implementation | Tradeoff / next step |
|---|---|---|
| Synthetic cohort only | Reproducible demo without patient data access; `datasets.generate` owns the artificial outcome | No external validity, clinical utility or real-world fairness conclusion |
| LR and bounded RF | Interpretable baseline plus nonlinear comparison; deterministic CPU training | Limited model search; no claim of SOTA |
| Train/validation/test separation | CV/scaling on train, threshold and selection on validation, test used for release gate | Repeated use of the same test set needs governance in a real program |
| Numeric JSON models | Avoid executable model deserialization; schema/topology checks and inference parity | Custom scorer maintenance; forest boundary regression required |
| DVC and MLflow together | DVC schedules reproducible outputs; MLflow records experiments/versions | Two identities must be cross-checked; local remote is not disaster recovery |
| PostgreSQL deployment pointer | Atomic pointer/audit/outbox and least-privilege serving role | Operator/database owner remains trusted; identity is locally asserted |
| Outbox for champion alias | Avoid claiming a distributed transaction; reconcile from current pointer | Eventual consistency; operator must retry reconciliation after alias outage |
| Explicit approval and rollback | Training/drift never changes deployment automatically | Manual response time; no autonomous remediation |
| Loopback Compose | Reproducible affordable integration lab | No HA, cloud IAM, autoscaling or internet security boundary |
| One large hash-locked environment | Windows/Linux dependency artifacts pinned and verified | Unused tools present in serving image; split locks are future work |
| Preserve v1 separately | Historical Flask/SQLite reference and regression coverage remain useful | Documentation must distinguish v1 and v2 routes, schemas and gates |
| Blocking dependency audit | Open advisories remain visible and prevent green CD | Local functional success does not produce release security clearance |

Original rationale is preserved in [ADRs](../adr/0001-target-stack-and-legacy.md).
These decisions describe the current implementation, not a compliance certification.
