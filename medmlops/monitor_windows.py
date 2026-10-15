"""Real statistical calculations; Evidently integration remains a separate task."""
from typing import Any

import numpy as np
from scipy.stats import ks_2samp

from .datasets import FEATURES, Measurement
from .experiments import evaluate
from .scoring import predict


def matrix(frame):
    allowed = {*FEATURES, "synthetic_id", "target"}
    if not set(FEATURES) <= set(frame.columns) or not set(frame.columns) <= allowed:
        raise ValueError("Monitoring feature contract mismatch")
    for record in frame[list(FEATURES)].to_dict(orient="records"):
        Measurement(**record)
    return frame[list(FEATURES)].to_numpy(dtype=float)


def psi(reference, current):
    edges = np.unique(np.quantile(reference, np.linspace(.1, .9, 9)))
    bins = [-np.inf, *edges, np.inf]
    expected_counts = np.histogram(reference, bins=bins)[0]
    current_counts = np.histogram(current, bins=bins)[0]
    expected = (expected_counts + .5) / (expected_counts.sum() + len(expected_counts) * .5)
    actual = (current_counts + .5) / (current_counts.sum() + len(current_counts) * .5)
    return float(np.sum((actual - expected) * np.log(actual / expected)))


def monitor(bundle, reference, current, policy, labels=None, reference_metrics=None):
    rx, cx = matrix(reference), matrix(current)
    result: dict[str, Any] = {"reference_samples": len(rx), "current_samples": len(cx), "alerts": [],
              "automatic_training": False, "automatic_promotion": False,
              "clinical_validity": False, "evidently": "not executed"}
    if min(len(rx), len(cx)) < policy["min_samples"]:
        return {**result, "status": "inconclusive", "reason": "insufficient_window_size",
                "performance": {"status": "unavailable"}}
    data = {}
    # Bonferroni family-wise alpha; PSI supplies a minimum effect criterion.
    alpha = .05 / (len(FEATURES) + 1)
    for j, name in enumerate(FEATURES):
        test = ks_2samp(rx[:, j], cx[:, j])
        score = psi(rx[:, j], cx[:, j])
        alert = score >= policy["psi_threshold"] and float(test.pvalue) < alpha
        data[name] = {"psi": score, "ks_statistic": float(test.statistic),
                      "ks_pvalue": float(test.pvalue), "alert": alert}
        if alert:
            result["alerts"].append({"type": "data_drift", "feature": name})
    rp, cp = predict(bundle, rx), predict(bundle, cx)
    prediction_test = ks_2samp(rp, cp)
    prediction_psi = psi(rp, cp)
    prediction_alert = prediction_psi >= policy["psi_threshold"] and prediction_test.pvalue < alpha
    if prediction_alert:
        result["alerts"].append({"type": "prediction_drift"})
    performance: dict[str, Any] = {"status": "unavailable", "reason": "reliable_labels_not_supplied"}
    if labels is not None:
        y = np.asarray(labels)
        if len(y) != len(cx) or y.ndim != 1 or not np.isin(y, [0, 1]).all():
            raise ValueError("Invalid or misaligned labels")
        if len(np.unique(y)) != 2:
            performance = {"status": "inconclusive", "reason": "one_label_class"}
        else:
            performance = {"status": "measured", "metrics": evaluate(y, cp, bundle["threshold"])}
            if reference_metrics is not None:
                difference = reference_metrics["auc"] - performance["metrics"]["auc"]
                performance["auc_drop"] = float(difference)
                if difference >= policy["auc_drop"]:
                    result["alerts"].append({"type": "performance_degradation",
                                             "note": "Observed AUC decrease; operator investigation required"})
    return {**result, "status": "evaluated", "data_drift": data,
            "prediction_drift": {"psi": prediction_psi, "ks_pvalue": float(prediction_test.pvalue),
                                 "alert": bool(prediction_alert)},
            "performance": performance,
            "statistics": {"method": "two-sample KS + PSI effect gate", "corrected_alpha": alpha}}
