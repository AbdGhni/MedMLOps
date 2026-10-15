"""Read-only Windows diagnostic. Never changes ACLs, proxies or security policy."""
import configparser
import hashlib
import importlib.metadata
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE_COMMIT = "[private-revision]"
ARCHIVE_HASH = "7fcb877432c7ac6942dd7ae18dcf0c5bca8c879c4816f69a5029803b09be2039"


def command(args):
    try:
        result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, timeout=10)
        return {"command": args, "exit_code": result.returncode,
                "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"command": args, "error": type(error).__name__}


def main():
    report = {"executed_at": datetime.now(timezone.utc).isoformat(), "repository": str(ROOT),
              "python": sys.version.split()[0], "python_executable": sys.executable,
              "policy_changed": False, "pip_no_index": os.environ.get("PIP_NO_INDEX"),
              "proxy_environment": {}, "dns": {}, "pip_config_files": []}
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"):
        value = os.environ.get(key) or os.environ.get(key.lower())
        if value:
            parsed = urllib.parse.urlsplit(value)
            report["proxy_environment"][key] = {"host": parsed.hostname, "port": parsed.port,
                                                 "credentials_present": bool(parsed.username or parsed.password)}
    for host in ("pypi.org", "files.pythonhosted.org"):
        try:
            report["dns"][host] = {"addresses": sorted({v[4][0] for v in socket.getaddrinfo(host, 443)})}
        except OSError as error:
            report["dns"][host] = {"error_type": type(error).__name__, "code": error.errno}
    try:
        # Uses existing proxy and default TLS verification. No fallback/direct bypass.
        with urllib.request.urlopen("https://pypi.org/pypi/fastapi/json", timeout=5) as response:
            report["pypi_https"] = {"status": response.status, "tls": "verified by default client"}
    except urllib.error.URLError as error:
        reason = error.reason
        report["pypi_https"] = {"error_type": type(reason).__name__,
                                "code": getattr(reason, "winerror", getattr(reason, "errno", None)),
                                "tls": "not verified; connection failed before a successful request"}
    paths = [Path("C:/ProgramData/pip/pip.ini"), Path.home() / "pip/pip.ini", ROOT / ".venv/pip.ini"]
    if os.environ.get("APPDATA"):
        paths.append(Path(os.environ["APPDATA"]) / "pip/pip.ini")
    for path in paths:
        item = {"path": str(path), "exists": path.exists()}
        if path.exists():
            parser = configparser.ConfigParser()
            parser.read(path)
            item["keys"] = {section: list(parser[section]) for section in parser.sections()}
        report["pip_config_files"].append(item)
    installed = {d.metadata["Name"].lower(): d.version for d in importlib.metadata.distributions()}
    names = ["numpy", "pandas", "scipy", "scikit-learn", "pydantic", "fastapi", "uvicorn",
             "mlflow", "dvc", "evidently", "pytest", "ruff", "mypy", "pip-audit", "prometheus-client", "psycopg"]
    report["packages"] = {n: installed.get(n, "NOT_INSTALLED") for n in names}
    report["commands"] = [command(args) for args in (
        ["git", "rev-parse", "HEAD"], ["git", "status", "--short"],
        ["git", "cat-file", "-t", BASE_COMMIT], ["git", "--version"],
        [sys.executable, "-m", "pip", "--version"],
        ["docker", "version"], ["docker", "compose", "version"],
    )]
    virtual_python = ROOT / ".venv/Scripts/python.exe"
    if virtual_python.exists():
        report["venv_core_imports"] = command([str(virtual_python), "-c",
            "import numpy,pandas,sklearn,pydantic; print('core imports OK')"])
    archive = ROOT.parent / "MedMLOps-v2-core.zip"
    if archive.exists():
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        with zipfile.ZipFile(archive) as zipped:
            report["archive"] = {"sha256": digest, "expected_match": digest == ARCHIVE_HASH,
                                  "crc_ok": zipped.testzip() is None}
    report["limitations"] = ["No firewall or ACL modification", "TLS cannot be inferred from DNS",
                              "Package installation and Docker integration not performed"]
    target = ROOT / "docs/validation/phase3-diagnostic.json"
    target.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"evidence": str(target), "pypi_https": report["pypi_https"],
                      "archive": report.get("archive"), "policy_changed": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
