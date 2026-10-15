# Reproducible 5–10 minute demonstration

## Prepare before the interview

Use a clean committed checkout, Python 3.12 and Docker Desktop Linux engine.
Complete installation/build before the timed presentation. From repository root:

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install --index-url https://pypi.org/simple pip==26.2.1
.venv/Scripts/python.exe -m pip install --index-url https://pypi.org/simple --require-hashes -r requirements-target.lock
.venv/Scripts/python.exe -m scripts.bootstrap_local
.venv/Scripts/python.exe -m medmlops.pipeline all --work runtime/phase4
docker compose up --build -d --wait --wait-timeout 240
$env:MEDMLOPS_EVIDENCE_DIR = 'runtime/demo-evidence'
.venv/Scripts/python.exe -m scripts.check_tracking
```

Stop if any command fails. Approval requires clean training provenance. Check
`git status --short` before training; do not hide modifications to pass this gate.
Use the existing `.env` credentials locally without putting them into slides,
terminal recordings, committed screenshots or browser URLs. Grafana user is admin.

## Presentation sequence

| Time | Show | Explain |
|---|---|---|
| 0:00–0:45 | README architecture and synthetic-only notice | Traceability and controlled change; no medical use |
| 0:45–1:30 | `runtime/phase4/dataset.json`, `validation.json`, prepared manifest | Seed, content hash, schema, subject splits |
| 1:30–2:30 | `comparison.json`; MLflow at http://127.0.0.1:5000 | Train CV, validation selection, held-out AUC, params/artifacts and run provenance |
| 2:30–3:15 | MLflow registered model `synthetic-event-v2`; lifecycle history | Candidate publication differs from explicit approval; PG pointer is deployment truth |
| 3:15–4:00 | http://127.0.0.1:8000/docs and authenticated prediction from command below | Strict request contract; actual version/digest; no raw patient values in audit |
| 4:00–5:00 | http://127.0.0.1:3000/d/medmlops-v2 | Throughput, p95/p99, served version, governance state |
| 5:00–7:30 | Run acceptance below; inspect current Evidently reports and Prometheus `/alerts` | Stable window, synthetic shift, labelled degradation, persisted incident and firing rule |
| 7:30–9:00 | E2E evidence and lifecycle history | Rejected constant model, challenger, verified rollback, outage compensation and persistence |
| 9:00–10:00 | LIMITATIONS and security report | Open advisories, local identity, remote CI/captures pending; next engineering priorities |

```powershell
.venv/Scripts/python.exe -m scripts.validate_phase4
.venv/Scripts/python.exe -m medmlops.lifecycle history
.venv/Scripts/python.exe -m scripts.check_dvc
```

The E2E command injects faults and recreates containers without deleting volumes.
It can exceed the allotted demo slot; run it beforehand and present its authentic
JSON/log evidence if time is short. Do not describe replayed evidence as live.
It ends on the approved selected model; the drift alert remains visible from the
last evaluated degraded window. Rollback does not erase an incident.

## Authenticated API example

This Python command loads credentials internally and prints only response data:

```powershell
.venv/Scripts/python.exe -c "import os,httpx; from medmlops.settings import load_local; from medmlops.datasets import generate,FEATURES; load_local(); r=generate(500).iloc[0][list(FEATURES)].to_dict(); r.update({k:int(r[k]) for k in ('sex_code','prior_event')}); x=httpx.post('http://127.0.0.1:8000/predict',headers={'Authorization':'Bearer '+os.environ['MEDMLOPS_API_TOKEN']},json={'records':[r]}); x.raise_for_status(); print(x.json())"
```

Manual rollback uses the existing approval, not an invented version number:

```powershell
$version = Read-Host 'Existing approved MLflow version from lifecycle history'
.venv/Scripts/python.exe -m medmlops.lifecycle rollback --version $version --actor local-operator
```

## Authentic capture checklist

No authorized browser surface was available during Phase 5 inventory. No screenshots
are fabricated or claimed. Capture manually after running this stack:

- [ ] Dataset manifest and validation result (terminal, current commit visible).
- [ ] MLflow experiment comparison with run IDs, params and held-out metrics.
- [ ] Registry versions/tags and candidate/approval/deployment audit correspondence.
- [ ] Swagger request schema plus actual successful authenticated HTTP response.
- [ ] Grafana nine-panel dashboard with time range and populated series.
- [ ] Prometheus http://127.0.0.1:9090/targets and `/alerts` showing real scrape/firing state.
- [ ] Open the actual `.html` files under `runtime/phase4/reports` in a browser:
  stable versus shifted report; match folder IDs to `runtime/demo-evidence/end-to-end.json`.
- [ ] Rollback history and `/model/info` showing the restored approved version.

Store reviewed images in `docs/portfolio/screenshots/`, with capture date, commit,
scenario/run/version and caption. Exclude credentials, browser autofill and tokens.
Add README image links only once the corresponding files actually exist.
