# ADR 0001 — Target stack, legacy prototype and integration boundary

Status: implemented and locally service-verified in Phase 4. Date: 2026-10-14.

Phase 4 evidence: `../validation/phase4/end-to-end.json`. The stable top-level
package is preserved to avoid unnecessary disruption of the v2 core. MLflow now
stores the numeric bundle with a tested pyfunc flavor; Flask remains legacy only.
Security release and rendered-browser portfolio checks are still open; see the
Phase 4 status rather than the historical pending statements below.

## Context
The initial prototype used Flask, SQLite, a numeric JSON model and five synthetic features. The expanded specification explicitly requires FastAPI, MLflow, DVC, PostgreSQL, Evidently, Prometheus and Grafana. The prototype does not satisfy those requirements.

## Decision
Implement the requested stack. Retain the original code as a tested v1 reference while building v2 stages separately. Flask/SQLite are **not substitutes** for FastAPI/PostgreSQL/MLflow. No v2 candidate is served by the v1 API. Only successful real service integration tests can complete those tickets.

MVP: CPU classification; synthetic snapshots; LR/RF; DVC stages; MLflow Tracking/Registry on PostgreSQL with a persistent local artifact volume; explicit approval and deployed-version pointer; FastAPI/Pydantic; labelled monitoring; Evidently; Prometheus/Grafana; audit and rollback; CI, explicit CT and controlled CD. MinIO is optional: a local artifact volume avoids an unnecessary S3 service for a single-host demonstration. PyTorch, Optuna, cloud/Kubernetes, HA and real healthcare data remain extensions.

Numeric JSON inference is retained as an artifact format, not a registry replacement. It avoids executable deserialization; both LR and RF are tested against sklearn predictions. MLflow can store this bundle and a pyfunc flavor after actual MLflow integration is available. Hashes detect integrity failures but are not signatures.

## Repository layout
Keep the existing top-level `medmlops/` Python package until bootstrap can be tested in an isolated installation. The proposed `src/` relocation is deferred to ticket MM-002 rather than simultaneously breaking the verified legacy commands. Add `configs`, `api`, `pipelines`, `infrastructure`, `docs/architecture`, `docs/adr`, `docs/runbooks`, `docs/validation` and test lanes as implemented. Do not create empty modules and call them implemented.

## Consequences
Two clearly named contracts coexist: `synthetic-risk-v1` (legacy) and `synthetic-event-v2` (target). Target readiness must reject the wrong schema. The English README identifies these boundaries. Migration and integration remain open until dependencies and Docker are available.
