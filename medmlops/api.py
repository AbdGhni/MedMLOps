"""Authenticated loopback demo API. No raw inputs are logged or persisted."""
import hmac
import os
import time
from functools import wraps
from pathlib import Path

from flask import Flask, jsonify, request, send_file
from werkzeug.exceptions import HTTPException

from .data import validate
from .model import drift, predict
from .store import Store


def create_app(root="runtime", token=None):
    token = token or os.environ.get("MEDMLOPS_API_TOKEN")
    if not token or len(token) < 16:
        raise ValueError("MEDMLOPS_API_TOKEN must contain at least 16 characters")
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024
    store = Store(root)

    def protected(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            supplied = request.headers.get("Authorization", "")
            if not hmac.compare_digest(supplied.encode(), ("Bearer " + token).encode()):
                return jsonify(error="Unauthorized"), 401
            return fn(*args, **kwargs)
        return wrapped

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        return response

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.name), error.code

    @app.errorhandler(Exception)
    def internal_error(error):
        # Never echo inputs, credentials, filesystem paths or exception details.
        return jsonify(error="Operation failed"), 500

    @app.get("/")
    def dashboard():
        return send_file(Path(__file__).parent / "static" / "index.html")

    @app.get("/health/live")
    def live():
        return jsonify(status="alive", purpose="synthetic demonstration")

    @app.get("/health/ready")
    def ready():
        try:
            version, _ = store.load()
            return jsonify(status="ready", version=version)
        except (LookupError, ValueError, OSError):
            return jsonify(status="not_ready"), 503

    @app.get("/api/status")
    @protected
    def status():
        return jsonify(store.status())

    def get_records():
        payload = request.get_json()
        if not isinstance(payload, dict) or set(payload) != {"records"}:
            raise ValueError("Expected records envelope")
        return validate(payload["records"])

    @app.post("/api/predict")
    @protected
    def inference():
        start = time.perf_counter()
        try:
            x = get_records()
        except ValueError:
            return jsonify(error="Invalid feature contract"), 422
        try:
            version, bundle = store.load()
        except (LookupError, ValueError, OSError):
            return jsonify(error="No verified active model"), 503
        probabilities = predict(bundle, x)
        elapsed = (time.perf_counter() - start) * 1000
        store.audit("prediction", version, {"count": len(x), "latency_ms": elapsed})
        return jsonify(version=version, threshold=bundle["threshold"], latency_ms=elapsed,
                       purpose="Synthetic research only; not a clinical decision",
                       predictions=[{"probability": float(p), "flag": bool(p >= bundle["threshold"])}
                                    for p in probabilities])

    @app.post("/api/monitor")
    @protected
    def monitoring():
        try:
            x = get_records()
        except ValueError:
            return jsonify(error="Invalid feature contract"), 422
        if len(x) < 100:
            return jsonify(error="Monitoring requires at least 100 records"), 422
        try:
            version, bundle = store.load()
        except (LookupError, ValueError, OSError):
            return jsonify(error="No verified active model"), 503
        report = drift(bundle, x)
        store.audit("monitoring", version, report)
        return jsonify(version=version, **report)

    return app
