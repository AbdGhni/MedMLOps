# CV bullets

- Built a reproducible local ML platform on synthetic healthcare data using DVC, MLflow, PostgreSQL, FastAPI and Docker Compose, with explicit dataset and model provenance.
- Implemented controlled model approval, transactional deployment auditing and verified rollback, including failed-deployment compensation and artifact-corruption checks.
- Compared logistic regression and random forest using disjoint train/validation/test splits, five-fold training CV and numeric train/serve parity; recorded 0.867 held-out ROC-AUC on the synthetic reference fixture.
- Integrated Evidently reports, Prometheus metrics/alerts and a provisioned Grafana dashboard to distinguish distribution shift from labelled performance degradation.
- Added regression tests and prepared CI/manual training/controlled deployment workflows while retaining a blocking dependency audit and documenting unresolved transitive vulnerabilities.

Use the current final report for the verified test count. Do not add claims about
patient benefit, production traffic, cloud deployment, compliance certification or
a completely green target CI. Remote core/legacy checks passed, while target CI
remains blocked by its dependency audit.
