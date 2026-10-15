"""Versioned synthetic cohort and shared training/serving contract."""
import hashlib
import json

import numpy as np

SCHEMA_VERSION = "synthetic-risk-v1"
FEATURES = ("age", "heart_rate", "systolic_bp", "oxygen_saturation", "temperature")
BOUNDS = ((18, 100), (40, 180), (70, 220), (80, 100), (35, 42))


def validate(records):
    if not isinstance(records, list) or not 1 <= len(records) <= 1000:
        raise ValueError("Expected 1 to 1000 records")
    rows = []
    for record in records:
        if not isinstance(record, dict) or set(record) != set(FEATURES):
            raise ValueError("Feature schema mismatch; identifiers are prohibited")
        row = []
        for name, (lo, hi) in zip(FEATURES, BOUNDS, strict=True):
            value = record[name]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(f"{name}: numeric value required")
            if not np.isfinite(value) or not lo <= value <= hi:
                raise ValueError(f"{name}: outside supported range [{lo}, {hi}]")
            row.append(value)
        rows.append(row)
    return np.asarray(rows, dtype=float)


def generate(n=4000, seed=42, shifted=False):
    if n < 500:
        raise ValueError("At least 500 synthetic subjects required")
    rng = np.random.default_rng(seed)
    x = np.column_stack([
        rng.uniform(18, 90, n), rng.normal(85, 18, n),
        rng.normal(125, 20, n), rng.normal(96, 2.5, n), rng.normal(37, 0.7, n),
    ])
    if shifted:
        x[:, 1] += 25
        x[:, 3] -= 5
    for j, (lo, hi) in enumerate(BOUNDS):
        x[:, j] = np.clip(x[:, j], lo, hi)
    logits = (-1.7 + 0.025 * (x[:, 0] - 50) + 0.065 * (x[:, 1] - 85)
              - 0.05 * (x[:, 2] - 125) - 0.55 * (x[:, 3] - 96)
              + 0.8 * (x[:, 4] - 37))
    y = (rng.random(n) < 1 / (1 + np.exp(-logits))).astype(int)
    return x, y


def fingerprint(x, y):
    return hashlib.sha256(x.astype("<f8").tobytes() + y.astype("<i8").tobytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
