# MedMLOps — project overview

MedMLOps demonstrates how an ML engineer can turn an experiment into a traceable,
operable local service. The scenario is prediction of an artificial healthcare
event from ten synthetic measurements. No real patient data is used, no clinical
validation was performed, and predictions must not guide care.

The engineering problem is keeping data, experiments, artifacts, approvals and
the model actually served consistent. In a MedTech/pharmaceutical setting these
are relevant foundations for reviewability, incident response and controlled
change. This project does not claim GxP, HIPAA, GDPR, MDR or FDA certification.

The implementation combines Python/scikit-learn, a DVC DAG, MLflow Tracking and
Registry, PostgreSQL approval and audit tables, authenticated FastAPI inference,
Evidently reports, Prometheus metrics/alerts and provisioned Grafana dashboards.
Docker Compose supplies the local integration environment. GitHub definitions
separate CI, manually requested training and reviewer-controlled deployment.

The reference experiment uses 4,000 generated subjects with disjoint 60/20/20
partitions. Five-fold training CV and validation-only model selection choose
logistic regression; its recorded held-out ROC-AUC is 0.86698 versus 0.83770
for the bounded random forest. These values measure this artificial fixture only.

Evidence includes real service integration, rejected candidates, train/serve
parity, drift incidents, a firing alert, rollback, failed-deployment compensation
and container recreation with persistent volumes. See the current
[final report](../validation/phase5/FINAL_REPORT.md) for checks actually rerun.
The original [Phase 4 evidence](../validation/phase4/status.md) is preserved.

Suggested recruiter reading: README → [technical deep dive](TECHNICAL_DEEP_DIVE.md)
→ [demo](DEMO_SCRIPT.md) → [limitations](LIMITATIONS.md). The strongest discussion
is about reproducibility, deployment authority and failure recovery, rather than
claiming a clinically useful classifier or enterprise production readiness.
