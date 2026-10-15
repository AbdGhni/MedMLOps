# Target architecture diagrams

These diagrams describe the locally implemented v2 stack. Executed service evidence
and remaining release restrictions are in `docs/validation/phase4/status.md` and
`docs/validation/phase5/FINAL_REPORT.md`. They do not imply a cloud or clinical deployment.

## Global architecture
```mermaid
flowchart LR
  G[Synthetic generator] --> V[Data validation]
  V --> D[DVC snapshots and DAG]
  D --> F[Feature preparation]
  F --> T[LR and RF training]
  T --> E[Evaluation and gate]
  T --> M[MLflow Tracking]
  E --> R[MLflow Registry]
  R --> A[Explicit approval]
  A --> C[Deployment controller]
  C --> S[FastAPI serving]
  C --> P[(PostgreSQL audit and deployment)]
  M --> P
  S --> N[Monitoring engine]
  N --> I[Incidents and alerts]
  S --> PR[Prometheus]
  N --> PR
  C --> PR
  PR --> GR[Provisioned Grafana]
```

## Data flow
```mermaid
flowchart LR
  SE[Seed and config in Git] --> RAW[Immutable synthetic CSV and manifest]
  RAW --> Q[Schema and quality checks]
  Q --> SPLIT[Disjoint subject split 60 / 20 / 20]
  SPLIT --> TR[Train]
  SPLIT --> VA[Validation]
  SPLIT --> TE[Test]
  TR --> CV[CV within train]
  CV --> FIT[Final fitting on train]
  FIT --> VA
  VA --> TH[Threshold and model selection]
  TH --> TE
  TE --> REPORT[Metrics and evidence]
```

## Model lifecycle
```mermaid
stateDiagram-v2
  [*] --> Training
  Training --> Evaluation
  Evaluation --> ValidationGate
  ValidationGate --> Rejected: failed checks
  ValidationGate --> Candidate: passed checks
  Candidate --> Approved: explicit actor decision
  Approved --> Champion: controlled deploy and verify
  Champion --> PreviousApproved: superseded
  PreviousApproved --> Champion: rollback and verify
  Rejected --> [*]
```

## Training sequence
```mermaid
sequenceDiagram
  participant O as Operator/explicit CT
  participant D as DVC
  participant T as Training
  participant M as MLflow
  participant G as Gate
  O->>D: reproduce commit + parameters
  D->>T: verified disjoint partitions
  T->>T: CV, fit, validation selection, test
  T->>M: parameters, dataset, commit, metrics, artifacts
  T->>G: candidate report and hash
  G->>G: verify integrity and acceptance
  G-->>O: Candidate or Rejected; no auto-promotion
```

## Deployment sequence
```mermaid
sequenceDiagram
  participant O as Actor
  participant C as Controller
  participant M as MLflow Registry
  participant P as PostgreSQL
  participant S as FastAPI
  O->>C: approve pinned version
  C->>M: fetch candidate and artifacts
  C->>C: validate gate, hash and schema
  C->>P: atomic deployment pointer + audit + outbox
  S->>P: resolve pinned deployment
  S->>S: load verified artifact
  C->>S: readiness + smoke prediction + version
  C->>M: reconcile champion alias
  C-->>O: verified deployment or compensating failure
```

## Rollback sequence
```mermaid
sequenceDiagram
  participant O as Operator
  participant I as Incident log
  participant C as Rollback controller
  participant P as PostgreSQL
  participant S as FastAPI
  O->>I: register incident and active version
  O->>C: select earlier approved version
  C->>C: verify approval, schema and hash
  C->>P: atomic pointer switch + audit
  C->>S: readiness and prediction
  S-->>C: actual served version
  alt restored version confirmed
    C->>I: record rollback success
  else verification failed
    C->>P: compensating pointer switch + audit
    C->>I: escalate verification failure
  end
```

## Monitoring architecture
```mermaid
flowchart LR
  REF[Versioned training reference] --> ENG[Monitoring window engine]
  CUR[Current synthetic window] --> ENG
  LAB[Reliable labels when available] --> ENG
  ENG --> DD[Data PSI and KS]
  ENG --> PD[Prediction distribution shift]
  ENG --> PERF[Labelled AUC, F1, Brier and confusion]
  ENG --> EV[Evidently HTML and JSON report]
  DD --> ALERT[Alert policy and incident history]
  PD --> ALERT
  PERF --> ALERT
  API[FastAPI latency/errors/version] --> PROM[Prometheus]
  ALERT --> PROM
  PROM --> GRAF[Grafana dashboard]
  ALERT --> HUMAN[Operator investigation; no automatic retrain]
```
