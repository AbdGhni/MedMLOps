# Technical deep dive

## Data and experiment boundaries

`datasets.py` generates a seeded artificial outcome and ten bounded features.
Snapshots use canonical CSV bytes, SHA256 identity and exclusive creation;
loading rechecks the hash, manifest and schema. Names and unexpected fields are
forbidden by strict Pydantic prediction schemas. Synthetic IDs are used for
partition checks and never accepted as inference features.

`experiments.prepare` creates stratified 60/20/20 subject partitions and hashes
the prepared NPZ. `experiments.run` verifies that hash and subject disjointness.
StandardScaler is inside the logistic sklearn pipeline, so CV fits it on each
training fold. Forest depth, tree count and leaf support are bounded. Five-fold
CV uses training only; the threshold is selected on validation data for a target
sensitivity of .85, then the candidate is selected by validation ROC-AUC.

Held-out AUC, PR-AUC, average precision, sensitivity, specificity, F1, Brier,
confusion and calibration are reported. The held-out test set gates acceptance,
not algorithm selection. Repeated acceptance on one fixed fixture is still an
adaptive evaluation risk; a real release needs an independently governed dataset.
The age-slice and bootstrap analyses in `train.py` belong to the preserved v1
reference; they are not claimed as additional v2 approval gates.

## Reproduction and provenance

`dvc.yaml` defines generate → validate → prepare → train → evaluate. Git stores
parameters/DAG/lock; a local DVC cache/remote stores outputs outside Git. The
checker exercises no-op, forced reproduction, seed invalidation and previous
output checkout. This is a local recovery demonstration, not remote disaster recovery.

Reports retain Git commit/dirty state, selected source hashes, dependency versions,
dataset and model identity. Controlled approval rejects dirty-training evidence.
The source hash covers the mathematical training modules; it is not a complete
environment attestation. The distribution lock carries artifact hashes, while
numeric equality is demonstrated on one platform, not promised across hardware.

## Registry and deployment authority

`tracking.publish` recomputes held-out candidate metrics before publishing numeric
JSON bundles, reports and verification to actual MLflow runs and versions.
Failed quality candidates can be logged; publication does not grant approval.
`governance.approve` applies the local operator's policy rather than uploaded
thresholds and checks evidence consistency before storing the approval.

`deployment` in PostgreSQL is authoritative. A row lock serializes switches;
pointer, audit and outbox commit together. `reconcile` updates MLflow's champion
alias from the current pointer. This handles a cross-system operation without
pretending PostgreSQL and MLflow share one transaction.

`verified_switch` fetches a pinned version, checks the approved digest, switches,
then sends readiness and prediction HTTP probes. Failure restores the prior
approval using a generation guard. A later concurrent deployment cannot be
silently overwritten by stale compensation. An alias failure remains retryable.

## Serving and observability

`serving.Loader` resolves the current approval and verifies local model bytes on
every request. Corruption gives 503. Scoring uses numeric JSON, with a trusted
installed MLflow loader; it does not deserialize model pickle. Forest inference
casts inputs to float32 and compares Python float thresholds to match sklearn's
C-double branch semantics under NumPy 2.

Authentication uses constant-time byte comparison. Validation errors are generic,
body size is capped and request IDs are bounded. The serving database role can
read deployment metadata and append aggregate events, not approve/deploy. If
prediction audit insertion fails, the API fails closed with 503.

Monitoring combines KS with Bonferroni correction and a PSI effect threshold.
Prediction drift and labelled AUC loss are distinct signals. Small windows are
inconclusive; without labels performance is unavailable. Evidently writes real
HTML/JSON reports; PostgreSQL stores aggregate incidents. Prometheus scrapes
request counts, latency, model version, governance availability and drift state;
Grafana provisions nine panels. No notification delivery or automatic retraining
is configured. See [security review](../validation/phase5/SECURITY_REVIEW.md) for
trust assumptions and unresolved vulnerabilities.
