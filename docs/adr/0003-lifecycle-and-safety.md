# ADR 0003 — Controlled lifecycle and simulated safety criteria

Status: implemented and verified against MLflow/PostgreSQL/FastAPI locally.

Phase 4 evidence demonstrates actor approval, transactional pointer/audit/outbox,
generation-guarded compensation, alias reconciliation, actual HTTP version checks,
rejected-candidate denial, corruption denial and successful rollback. The API role
cannot update the deployment pointer. Actor strings represent a local trusted
operator assertion; enterprise identity is not claimed. MLflow is loopback-only.

Lifecycle: Training → Evaluation → Validation Gate → Candidate → Approved → Champion. An explicit actor approval is required between candidate and approved; passing training alone never promotes. Demo gate: AUC ≥ .78, sensitivity ≥ .75, specificity ≥ .40, Brier ≤ .20, train/serve difference ≤ 1e-12. These are exercise thresholds: they catch random prediction, excessive misses and excessive false alarms without claiming clinical standards. Baseline is LR; RF is a bounded challenger. Select by validation ROC-AUC; test is a one-time evaluation, not a tuning signal. Cross-validation occurs within train with preprocessing inside each fold.

MLflow aliases identify registry roles; they are not deployment. The target service must load a pinned approved model version, check its artifact hash and schema, and confirm the served version. Deployment uses a PostgreSQL transaction with actor, time, checks and audit event; an external MLflow alias update cannot share that transaction, so use a compensating event/outbox and reconciliation. Readers retain their immutable version for in-flight requests. Rollback accepts a previous approved, verified version, atomically switches the deployment pointer, then checks readiness and a prediction. Verification failure must trigger a compensating switch and incident event.

Separate data drift, prediction drift, labelled performance change and operational faults. Drift alerts do not train or promote. A deliberately failed candidate must be rejected by the gate; the rollback drill is a separate approved deployment incident scenario and must never bypass approval to deploy a rejected artifact.

Only synthetic records are permitted. No clinical recommendations, certification or regulatory compliance claims. Actor identities, correlation IDs and aggregate events are logged; tokens and raw feature values are excluded from operational logs. Retention design: retain all approved/champion artifacts for the MVP; retain rejected candidates and reports 30 days and incident/audit evidence 90 days. Implement no automatic purge until backup and audit requirements are verified.
