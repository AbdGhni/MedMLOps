"""FastAPI v2 serving: approved pinned artifacts, strict inputs, aggregate audit."""
import hashlib
import hmac
import os
import re
import threading
import time
import uuid
from pathlib import Path

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from fastapi.security import HTTPBearer
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest

from .candidate_validation import validate_structure
from .datasets import FEATURES, PredictionRequest
from .governance import Governance
from .scoring import predict
from .settings import load_local
from .tracking import fetch


class Loader:
    def __init__(self, governance, root):
        self.gov = governance
        self.root = Path(root)
        self.lock = threading.Lock()
        self.current = None

    def load(self):
        with self.lock:
            active = self.gov.active()
            if not active['version']:
                raise ValueError('No deployment')
            path = self.root / active['version'] / 'bundle' / 'model.json'
            if self.current is None or self.current[0] != active['version']:
                files, digest, _ = fetch(active['version'], self.root / active['version'])
                if digest != active['model_sha256']:
                    raise ValueError('Approved artifact mismatch')
                self.current = (active['version'], files['model.json'], digest, active['dataset'])
            # Check disk integrity on every request; corrupt cache never remains ready.
            payload = path.read_bytes()
            if hashlib.sha256(payload).hexdigest() != active['model_sha256']:
                raise ValueError('Cached artifact corrupted')
            validate_structure(self.current[1])
            return self.current


def create_app(governance=None, token=None, root=None):
    load_local()
    token = token or os.environ.get('MEDMLOPS_API_TOKEN', '')
    if len(token) < 16:
        raise ValueError('API token must contain at least 16 characters')
    gov = governance or Governance()
    loader = Loader(gov, root or os.getenv('MEDMLOPS_SERVING_ROOT', 'runtime/serving'))
    app = FastAPI(title='MedMLOps synthetic v2', version='2.0.0')
    registry = CollectorRegistry()
    requests = Counter('medmlops_requests_total', 'HTTP requests', ['route', 'status'], registry=registry)
    latency = Histogram('medmlops_request_seconds', 'HTTP latency', ['route'], registry=registry)
    version_gauge = Gauge('medmlops_model_info', 'Pinned approved model', ['version'], registry=registry)
    lifecycle = Gauge('medmlops_lifecycle_events', 'Persistent lifecycle events', ['action'], registry=registry)
    drift = Gauge('medmlops_drift_alert', 'Last evaluated window alert count', registry=registry)
    audit_available = Gauge('medmlops_audit_available', 'Governance database available', registry=registry)
    app.state.loader = loader
    app.state.registry = registry

    def auth(request: Request, _credentials=Depends(HTTPBearer(auto_error=False))):
        supplied = request.headers.get('Authorization', '')
        if not hmac.compare_digest(supplied.encode('utf-8'), f'Bearer {token}'.encode('utf-8')):
            raise HTTPException(401, 'Authentication required')
        return 'api-service'

    def deployed():
        try:
            current = loader.load()
            version_gauge.clear()
            version_gauge.labels(current[0]).set(1)
            return current
        except Exception:
            raise HTTPException(503, 'Approved deployment unavailable') from None

    @app.middleware('http')
    async def observe(request, call_next):
        started = time.monotonic()
        correlation = request.headers.get('X-Correlation-ID', '')
        if not re.fullmatch(r'[A-Za-z0-9._:-]{1,64}', correlation):
            correlation = uuid.uuid4().hex
        request.state.correlation = correlation
        # Bound actual bytes, including chunked requests; never trust Content-Length alone.
        if request.method == 'POST':
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 1024 * 1024:
                    return JSONResponse({'detail': 'Body too large'}, status_code=413)
            request._body = bytes(body)
        response = await call_next(request)
        route = request.scope.get('route')
        label = route.path if route else 'unmatched'
        requests.labels(label, str(response.status_code)).inc()
        latency.labels(label).observe(time.monotonic() - started)
        response.headers['X-Correlation-ID'] = correlation
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request, exc):
        # Pydantic's default error includes raw feature values; redact them.
        return JSONResponse({'detail': 'Invalid synthetic-event-v2 request'}, status_code=422)

    @app.get('/health')
    def health():
        return {'status': 'alive', 'synthetic_only': True}

    @app.get('/ready', dependencies=[Depends(auth)])
    def ready():
        current = deployed()
        return {'status': 'ready', 'version': current[0], 'model_sha256': current[2]}

    @app.get('/model/info', dependencies=[Depends(auth)])
    def info():
        current = deployed()
        return {'version': current[0], 'model_sha256': current[2], 'dataset_version': current[3],
                'schema': current[1]['schema'], 'kind': current[1]['kind'], 'clinical_validity': False}

    @app.post('/predict')
    def prediction(body: PredictionRequest, request: Request, actor=Depends(auth)):
        current = deployed()
        matrix = np.array([[getattr(record, f) for f in FEATURES] for record in body.records])
        probabilities = predict(current[1], matrix)
        try:
            gov.event(actor, 'prediction', current[0], {'count': len(probabilities)}, request.state.correlation)
        except Exception:
            raise HTTPException(503, 'Audit unavailable') from None
        return {'version': current[0], 'model_sha256': current[2],
                'probabilities': probabilities.tolist(),
                'classes': (probabilities >= current[1]['threshold']).astype(int).tolist(),
                'clinical_validity': False}

    @app.get('/metrics')
    def metrics():
        try:
            counts, alerts = gov.observability()
            for item in counts:
                lifecycle.labels(item['action']).set(item['count'])
            drift.set(alerts)
            audit_available.set(1)
        except Exception:
            audit_available.set(0)
        return Response(generate_latest(registry), media_type='text/plain; version=0.0.4')

    return app
