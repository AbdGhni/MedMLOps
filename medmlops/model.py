"""Numeric JSON inference; no executable model deserialization."""
import numpy as np

from .data import FEATURES, SCHEMA_VERSION


def predict(bundle, x):
    if bundle["schema"] != SCHEMA_VERSION or bundle["features"] != list(FEATURES):
        raise ValueError("Unsupported model schema")
    z = (x - np.asarray(bundle["mean"])) / np.asarray(bundle["scale"])
    logits = np.clip(z @ np.asarray(bundle["coef"]) + bundle["intercept"], -700, 700)
    return 1 / (1 + np.exp(-logits))


def drift(bundle, x):
    result = {}
    for j, name in enumerate(FEATURES):
        reference = bundle["reference"][name]
        edges = [-np.inf, *reference["edges"], np.inf]
        counts = np.histogram(x[:, j], bins=edges)[0]
        actual = (counts + 0.5) / (counts.sum() + 0.5 * len(counts))
        expected = np.asarray(reference["proportions"])
        psi = float(np.sum((actual - expected) * np.log(actual / expected)))
        result[name] = {"psi": psi, "alert": psi >= 0.2}
    return {"samples": len(x), "features": result,
            "alert": any(v["alert"] for v in result.values()),
            "interpretation": "Distribution shift only; no performance or clinical conclusion"}
