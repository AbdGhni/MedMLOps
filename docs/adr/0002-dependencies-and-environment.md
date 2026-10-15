# ADR 0002 — Dependency compatibility and environment blockers

Status: target hash lock and clean Linux container installation verified; security
release gate remains open. The paragraphs below record the historical Phase 3 audit.

Phase 4: authorized PyPI and Docker access work in
`C:/Projects/MedMLOps`. `requirements-target.lock` contains 213 pinned
distributions, with Windows/Linux markers and PyPI hashes. Fresh Docker installation,
venv `pip check`, 27 tests, Ruff and scoped Mypy passed. pip and Flask were updated
after the real audit. DiskCache/NLTK advisories remain without upstream fix versions;
the security gate is deliberately not waived. See `../validation/phase4/security.md`
and the recorded version/check reports. No sandbox or ACL bypass was used.

Python 3.12.4, NumPy 2.2.6, Pandas 2.3.3, scikit-learn 1.7.2, SciPy 1.14.1 and Pydantic 2.12.3 are installed and have been exercised together by the v2 tests. `requirements.txt` belongs to the prior prototype; it is not the target lock. `requirements-target.in` expresses candidate ranges only. Do not claim compatibility of the full target stack until a resolver and clean environment test succeed.

`python -m pip index versions fastapi --index-url https://pypi.org/simple --timeout 5 --retries 0` fails with “No matching distribution found”. MLflow, DVC, Evidently, FastAPI, Uvicorn, pytest, Ruff, Mypy and pip-audit are not installed in the audited interpreter. Docker CLI 29.8.2 and Compose 5.6.0 exist; the Linux engine named pipe is absent. Privileged resource queries are denied. Unprivileged queries report 16 logical CPUs and approximately 41.6 GiB free disk; available Docker RAM cannot be measured while the engine is stopped.

Once access is restored: resolve target requirements with a machine-readable report; install in a clean venv; run `pip check`, pytest, Ruff and pip-audit; generate a complete transitive lock including hashes. Select maintained versions after vulnerability review, not merely the first versions that resolve. Record report, versions and scan results under `docs/validation`. A network failure is not a vulnerability scan.

No mock service, manually invented lock, or local store is counted as an executed MLflow/DVC integration. Work on independent data, schema, evaluation and monitoring mathematics can proceed using installed dependencies.

Git checkout line endings are fixed to LF by `.gitattributes`, so source-file hashes are preserved across Windows checkouts rather than depending on `core.autocrlf`. This does not guarantee numerical identity across different CPU/library environments.
