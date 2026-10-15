# Phase 3 — Windows environment recovery

## Verified findings

The source is `C:/home/USER Initial HEAD was exactly `[private-revision]`. Archive SHA-256 matches `7fcb877432c7ac6942dd7ae18dcf0c5bca8c879c4816f69a5029803b09be2039`; CRC verification passes. A Git bundle at `runtime/MedMLOps-v2-backup.bundle` was created and `git bundle verify` reports a complete history. This backup is still temporary, not a completed durable migration.

The Windows user owns Projects, but the restricted Codex sandbox group has only ReadAndExecute. Creation of `Projects/MedMLOps` is denied. Documents and Local AppData expose the same sandbox restriction. Do not change ACLs, use elevation, or disable protections to force access. Local clone previously failed in Git's child shell with signal-pipe Win32 error 5. No Git URL rewrite was found; no successful cloned checkout is claimed.

DNS resolves both PyPI hosts. HTTP/HTTPS/ALL proxy environment values point to `127.0.0.1:9`, and `PIP_NO_INDEX=1` disables index use. Requests through the configured proxy fail with WinError 10061. This is consistent with the session's restricted network, not evidence of a PyPI outage. TLS negotiation never succeeds, so certificate validity cannot be established by this test. WinHTTP itself reports direct access; Python's environment proxy is a different setting. Firewall inspection is denied, so no firewall diagnosis is claimed. No pip.ini file was found in the inspected normal locations.

Python 3.12.4 and pip 25.2 work. Core packages are installed in the system interpreter. The existing `.venv` Python starts but cannot import NumPy, so it is not a usable core environment. Docker CLI 29.8.2 and Compose 5.6.0 exist; the engine pipe is absent, the Docker service is stopped and Desktop's status helper cannot write host logs from the sandbox. Starting or configuring the engine must be done from an authorized user context.

## User action: durable copy with history

Open a normal PowerShell window as your own user, without administrator elevation. Choose an authorized destination that does not already exist. Then run:

```powershell
& 'C:/home/USER `
  -Destination 'C:/Projects/MedMLOps'
```

Expected: full copy including `.git`, synthetic runtime artifacts and the Git bundle backup; identical source/destination HEAD; v2 base commit present; `git fsck --full` success and all tests passing. The current HEAD may include phase-3 additions, so the script verifies both current HEAD equality and continued presence of `[private-revision]`. It never moves or deletes the original, overwrites an existing destination, or copies ACLs. Failure retains source and partial destination for inspection. It excludes the two named rebuildable venvs and bytecode caches, not Git history or runtime evidence.

If script execution is blocked by your organization's execution policy, use its approved workflow; do not set ExecutionPolicy Bypass. A manual equivalent, only with a new empty destination, is:

```powershell
$source = 'C:/home/USER
$destination = 'C:/Projects/MedMLOps'
if (Test-Path -LiteralPath $destination) { throw 'Choose a new destination.' }
New-Item -ItemType Directory -Path $destination
robocopy $source $destination /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /XD .venv .venv-phase3 __pycache__
if ($LASTEXITCODE -ge 8) { throw 'Copy failed; retain both locations.' }
git -C $source rev-parse HEAD
git -C $destination rev-parse HEAD
git -C $destination cat-file -t [private-revision]
git -C $destination fsck --full
Set-Location -LiteralPath $destination
python -m unittest discover -s tests -v
```

The two HEAD values must match; `cat-file` must report `commit`; tests must succeed. Reopen the copied repository as the authorized Codex workspace. No ACL change is necessary for this procedure; if access is still denied, ask the workstation/workspace administrator for the approved location.

## User action: connectivity and Docker

From the authorized normal PowerShell context:

```powershell
Resolve-DnsName pypi.org
Resolve-DnsName files.pythonhosted.org
Invoke-WebRequest -Uri 'https://pypi.org/pypi/fastapi/json' -UseBasicParsing
Start-Process -FilePath 'C:\Program Files\Docker\Docker\Docker Desktop.exe' -WindowStyle Hidden
docker version
docker info --format '{{.NCPU}} {{.MemTotal}}'
docker compose version
```

Expected: DNS answers, HTTPS 200 with standard certificate verification, Docker client **and server**, and positive engine CPU/memory values. If these fail, use the approved network proxy, certificates and Docker installation support; do not disable TLS verification, firewall, endpoint security or managed proxy restrictions. Do not send credentials or full proxy URLs containing passwords.

For an offline approved environment, packages can instead be supplied through an approved wheelhouse containing compatible wheels and all transitive dependencies. That is an explicit offline install, not a fake integration; services and tests must still be run. The full target lock is not yet resolved, so no exact wheel list is asserted here.

If HTTPS access is authorized and works in the normal user context, prepare a **new** environment without deleting the old one:

```powershell
Set-Location -LiteralPath 'C:/Projects/MedMLOps'
if (Test-Path -LiteralPath '.venv-phase3') { throw 'Inspect the existing environment before reusing it.' }
python -m venv .venv-phase3
New-Item -ItemType Directory -Path runtime -Force
.venv-phase3\Scripts\python.exe -m pip install --dry-run --report runtime\target-resolution.json -r requirements-target.in
```

Expected: a successful resolver report, not an installed package. No managed proxy or index restriction is removed by these commands. Use your approved package index if an organization requires it. Dependency installation, lock generation and import/integration checks remain separate next steps after reviewing the report.

## Resume criteria

Resume target integration once the authorized workspace is writable, package installation is available through approved means, and the Docker server responds. Create a new isolated environment without deleting the old one. Resolve/lock dependencies, check imports and `pip check`, then execute actual MLflow/PostgreSQL, DVC, FastAPI, Evidently and monitoring service tests. Authentication alone never authorizes a GitHub push.
