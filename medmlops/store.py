"""Local immutable artifacts, transactional registry and aggregate audit."""
import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .data import canonical


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root):
        self.root = Path(root)
        (self.root / "models").mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY, created TEXT NOT NULL, report TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS registry (
                    slot TEXT PRIMARY KEY, model_id TEXT NOT NULL REFERENCES runs(id));
                CREATE TABLE IF NOT EXISTS audit (
                    seq INTEGER PRIMARY KEY, created TEXT NOT NULL, event TEXT NOT NULL,
                    model_id TEXT, detail TEXT NOT NULL);
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.root / "platform.sqlite", timeout=30)
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    def save(self, bundle, report):
        payload = canonical(bundle)
        version = hashlib.sha256(payload).hexdigest()
        path = self.root / "models" / f"{version}.json"
        try:
            with path.open("xb") as f:
                f.write(payload)
        except FileExistsError:
            if path.read_bytes() != payload:
                raise ValueError("Artifact collision or corruption") from None
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO runs VALUES (?, ?, ?)",
                       (version, now(), canonical(report).decode()))
        self.audit("training", version, {"passed": report["passed"]})
        return version

    def load(self, version=None):
        if version is None:
            with self.connect() as db:
                row = db.execute("SELECT model_id FROM registry WHERE slot='active'").fetchone()
            if not row:
                raise LookupError("No model promoted")
            version = row[0]
        if not re.fullmatch(r"[0-9a-f]{64}", version):
            raise ValueError("Invalid model version")
        payload = (self.root / "models" / f"{version}.json").read_bytes()
        if hashlib.sha256(payload).hexdigest() != version:
            raise ValueError("Model integrity check failed")
        return version, json.loads(payload)

    def promote(self, version, rollback=False):
        self.load(version)
        with self.connect() as db:
            row = db.execute("SELECT report FROM runs WHERE id=?", (version,)).fetchone()
            if not row or not json.loads(row[0])["passed"]:
                raise ValueError("Quality gate rejected this model")
            db.execute("INSERT INTO registry VALUES ('active', ?) "
                       "ON CONFLICT(slot) DO UPDATE SET model_id=excluded.model_id", (version,))
            db.execute("INSERT INTO audit(created,event,model_id,detail) VALUES (?,?,?,?)",
                       (now(), "rollback" if rollback else "promotion", version, "{}"))

    def audit(self, event, version, detail):
        with self.connect() as db:
            db.execute("INSERT INTO audit(created,event,model_id,detail) VALUES (?,?,?,?)",
                       (now(), event, version, canonical(detail).decode()))

    def status(self):
        with self.connect() as db:
            runs = [{"version": r[0], "created": r[1], "report": json.loads(r[2])}
                    for r in db.execute("SELECT * FROM runs ORDER BY created DESC")]
            active = db.execute("SELECT model_id FROM registry WHERE slot='active'").fetchone()
            audit = [{"seq": r[0], "created": r[1], "event": r[2], "version": r[3],
                      "detail": json.loads(r[4])}
                     for r in db.execute("SELECT * FROM audit ORDER BY seq DESC LIMIT 100")]
        return {"active": active[0] if active else None, "runs": runs, "audit": audit}
