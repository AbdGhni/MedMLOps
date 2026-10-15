# Windows PowerShell — currently verified core

Run from the existing MedMLOps Git checkout. Do not extract sources over an unrelated project. Python 3.12 is required.

```powershell
python --version
git status --short
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-core.txt
.venv/Scripts/python.exe -m medmlops.pipeline all
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m scripts.validate_v2
```

Installation commands above are the required clean-install procedure, **not an executed clean-install claim**. In the present environment PyPI is unavailable; tests and stages used the already installed system interpreter. Do not silently use a partially created venv. Use `python -m scripts.validate_v2` only after checking that the interpreter has the audited core dependencies.

The same validation command is wrapped by `scripts/Validate-Core.ps1`. Outputs go to ignored `runtime/verification-v2`; small evidence goes to `docs/validation/evidence-v2`. Datasets and fitted artifacts must not be committed.

The five stages are independently executable:

```powershell
python -m medmlops.pipeline generate
python -m medmlops.pipeline validate
python -m medmlops.pipeline prepare
python -m medmlops.pipeline train
python -m medmlops.pipeline evaluate
```

Prerequisites are enforced in order. A failed selected candidate returns exit code 2 from evaluate, writes its failed gate report and performs no promotion. Corrupt inputs or artifacts cause failure. `all` is an offline validation pipeline, not DVC/MLflow deployment.

Once dependencies are available, MM-002 resolves and locks the full target stack, then MM-004 initializes genuine DVC and executes `dvc repro`. Compose/MLflow/FastAPI/Grafana launch commands will be documented only after the corresponding integration has been built and tested. The existing `compose.yaml` starts the legacy prototype, not the target stack.

GitHub authentication and any push are separate from local development. No push is authorized by this guide.
