"""Real network smoke test; token comes only from environment."""
import json
import os
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

base = "http://127.0.0.1:8000"
with urllib.request.urlopen(base + "/health/ready", timeout=10) as response:
    assert response.status == 200
payload = {"records": [{"age": 68, "heart_rate": 105, "systolic_bp": 110,
                        "oxygen_saturation": 94, "temperature": 38}]}
request = urllib.request.Request(base + "/api/predict", data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ["MEDMLOPS_API_TOKEN"]})
with urllib.request.urlopen(request, timeout=10) as response:
    prediction = json.load(response)
    assert 0 <= prediction["predictions"][0]["probability"] <= 1
    assert len(prediction["version"]) == 64
evidence = Path(__file__).resolve().parents[1] / "docs" / "evidence" / "http-smoke.json"
evidence.parent.mkdir(parents=True, exist_ok=True)
evidence.write_text(json.dumps({"executed_at": datetime.now(timezone.utc).isoformat(),
                               "readiness": "PASS", "authenticated_prediction": "PASS",
                               "version": prediction["version"]}, indent=2), encoding="utf-8")
print("HTTP readiness + authenticated prediction: PASS")
