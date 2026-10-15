"""Sequential local HTTP latency; descriptive measurement, not a production SLA."""
import json
import os
import time
import urllib.request
from pathlib import Path

import numpy as np

payload = json.dumps({"records": [{"age": 68, "heart_rate": 105, "systolic_bp": 110,
                                   "oxygen_saturation": 94, "temperature": 38}]}).encode()
latencies = []
for i in range(110):
    request = urllib.request.Request("http://127.0.0.1:8000/api/predict", data=payload,
                                    headers={"Content-Type": "application/json", "Authorization":
                                             "Bearer " + os.environ["MEDMLOPS_API_TOKEN"]})
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=10) as response:
        assert response.status == 200
        json.load(response)
    if i >= 10:
        latencies.append((time.perf_counter() - start) * 1000)
report = {"mode": "100 sequential loopback requests; 10 warmups; SQLite audit enabled",
          "samples": len(latencies), "p50_ms": float(np.quantile(latencies, .5)),
          "p95_ms": float(np.quantile(latencies, .95)), "max_ms": max(latencies)}
path = Path("docs/evidence/http-benchmark.json")
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
