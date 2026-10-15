"""Synthetic-only v2 data contract, immutable snapshots and quality validation."""
import hashlib
import json
from pathlib import Path
from typing import Annotated

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from .data import canonical

SCHEMA = "synthetic-event-v2"
FEATURES = (
    "age", "sex_code", "creatinine", "crp", "heart_rate", "systolic_bp",
    "oxygen_saturation", "temperature", "bmi", "prior_event",
)
BOUNDS = ((18, 100), (0, 1), (0.3, 4), (0, 150), (40, 180),
          (70, 220), (80, 100), (35, 42), (15, 50), (0, 1))


class Measurement(BaseModel):
    """Strict feature contract; names/identifiers/unknown fields are forbidden."""
    model_config = ConfigDict(extra="forbid", strict=True, allow_inf_nan=False)
    age: Annotated[float, Field(ge=18, le=100)]
    sex_code: Annotated[StrictInt, Field(ge=0, le=1)]
    creatinine: Annotated[float, Field(ge=0.3, le=4)]
    crp: Annotated[float, Field(ge=0, le=150)]
    heart_rate: Annotated[float, Field(ge=40, le=180)]
    systolic_bp: Annotated[float, Field(ge=70, le=220)]
    oxygen_saturation: Annotated[float, Field(ge=80, le=100)]
    temperature: Annotated[float, Field(ge=35, le=42)]
    bmi: Annotated[float, Field(ge=15, le=50)]
    prior_event: Annotated[StrictInt, Field(ge=0, le=1)]


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    records: Annotated[list[Measurement], Field(min_length=1, max_length=1000)]


def generate(n=4000, seed=42, shifted=False):
    if n < 500:
        raise ValueError("Minimum synthetic cohort: 500")
    rng = np.random.default_rng(seed)
    x = np.column_stack([
        rng.uniform(18, 90, n), rng.integers(0, 2, n),
        rng.lognormal(0, .3, n), rng.gamma(2, 8, n),
        rng.normal(85, 18, n), rng.normal(125, 20, n),
        rng.normal(96, 2.5, n), rng.normal(37, .7, n),
        rng.normal(26, 4, n), rng.binomial(1, .2, n),
    ])
    if shifted:
        x[:, 4] += 25
        x[:, 6] -= 5
    for j, (low, high) in enumerate(BOUNDS):
        x[:, j] = np.clip(x[:, j], low, high)
    # Artificial event, with no claim about physiology or a real population.
    logits = (-2 + .025 * (x[:, 0] - 50) + .5 * (x[:, 2] - 1)
              + .02 * (x[:, 3] - 16) + .065 * (x[:, 4] - 85)
              - .05 * (x[:, 5] - 125) - .55 * (x[:, 6] - 96)
              + .8 * (x[:, 7] - 37) + .04 * (x[:, 8] - 26) + .7 * x[:, 9])
    frame = pd.DataFrame(x, columns=FEATURES)
    for name in ("sex_code", "prior_event"):
        frame[name] = frame[name].astype(int)
    frame.insert(0, "synthetic_id", [f"syn-{seed}-{i:06d}" for i in range(n)])
    frame["target"] = (rng.random(n) < 1 / (1 + np.exp(-logits))).astype(int)
    return frame


def validate(frame):
    if set(frame.columns) != {"synthetic_id", "target", *FEATURES}:
        raise ValueError("Dataset columns mismatch")
    if len(frame) < 500 or frame.isna().any().any():
        raise ValueError("Insufficient cohort or missing values")
    if frame.synthetic_id.duplicated().any() or not frame.synthetic_id.str.match(r"^syn-\d+-\d{6,}$").all():
        raise ValueError("Invalid or repeated synthetic subjects")
    if not set(frame.target.unique()) == {0, 1}:
        raise ValueError("Two binary target classes are required")
    for name, (low, high) in zip(FEATURES, BOUNDS, strict=True):
        if not pd.api.types.is_numeric_dtype(frame[name]) or not np.isfinite(frame[name]).all():
            raise ValueError(f"Invalid numeric column: {name}")
        if not frame[name].between(low, high).all():
            raise ValueError(f"Out-of-contract column: {name}")
    for name in ("sex_code", "prior_event"):
        if frame[name].dtype == bool or not set(frame[name].unique()) <= {0, 1}:
            raise ValueError(f"Nonbinary column: {name}")
    prevalence = float(frame.target.mean())
    if not .05 <= prevalence <= .8:
        raise ValueError("Demonstration class balance gate failed")
    return {"schema": SCHEMA, "samples": len(frame), "positives": int(frame.target.sum()),
            "prevalence": prevalence, "missing": 0, "duplicate_subjects": 0, "passed": True}


def snapshot(root, n=4000, seed=42):
    frame = generate(n, seed)
    validate(frame)
    csv = frame.to_csv(index=False, float_format="%.12g", lineterminator="\n").encode()
    version = hashlib.sha256(csv).hexdigest()
    folder = Path(root) / version
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "cohort.csv"
    try:
        with path.open("xb") as stream:
            stream.write(csv)
    except FileExistsError:
        if path.read_bytes() != csv:
            raise ValueError("Dataset snapshot corrupted") from None
    manifest = {"version": version, "schema": SCHEMA, "seed": seed, "n": n,
                "synthetic_only": True, "features": list(FEATURES)}
    (folder / "manifest.json").write_bytes(canonical(manifest))
    return manifest


def load_snapshot(root, version):
    if len(version) != 64 or any(c not in "0123456789abcdef" for c in version):
        raise ValueError("Invalid dataset version")
    folder = Path(root) / version
    payload = (folder / "cohort.csv").read_bytes()
    if hashlib.sha256(payload).hexdigest() != version:
        raise ValueError("Dataset integrity failed")
    manifest = json.loads((folder / "manifest.json").read_text())
    if manifest["version"] != version or manifest["schema"] != SCHEMA or not manifest["synthetic_only"]:
        raise ValueError("Dataset manifest mismatch")
    frame = pd.read_csv(folder / "cohort.csv")
    validate(frame)
    return frame, manifest
