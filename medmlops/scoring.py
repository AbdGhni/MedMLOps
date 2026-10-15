"""Numeric JSON scoring for Logistic Regression and bounded Random Forest."""
import numpy as np

from .datasets import FEATURES, SCHEMA


def predict(bundle, x):
    if bundle["schema"] != SCHEMA or bundle["features"] != list(FEATURES):
        raise ValueError("Model/data schema mismatch")
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[1] != len(FEATURES) or not np.isfinite(x).all():
        raise ValueError("Invalid scoring matrix")
    if bundle["kind"] == "logistic":
        scaled = (x - bundle["mean"]) / bundle["scale"]
        logits = np.clip(scaled @ np.asarray(bundle["coef"]) + bundle["intercept"], -700, 700)
        return 1 / (1 + np.exp(-logits))
    if bundle["kind"] != "forest" or not bundle["trees"]:
        raise ValueError("Unsupported model kind")
    # sklearn tree prediction converts inputs to float32 before branching.
    x = x.astype(np.float32)
    predictions = np.zeros(len(x))
    for tree in bundle["trees"]:
        for i, row in enumerate(x):
            node = 0
            visited = 0
            while tree["left"][node] != -1:
                visited += 1
                if visited > len(tree["left"]):
                    raise ValueError("Cyclic model tree")
                # NumPy 2 scalar promotion would round the double threshold to float32.
                # sklearn compares the float32 input as a C double against its threshold.
                node = (tree["left"][node] if float(row[tree["feature"][node]]) <= tree["threshold"][node]
                        else tree["right"][node])
            predictions[i] += tree["positive_probability"][node]
    return predictions / len(bundle["trees"])


def export_model(pipeline, kind):
    base = {"schema": SCHEMA, "features": list(FEATURES), "kind": kind}
    if kind == "logistic":
        scaler = pipeline.named_steps["standardscaler"]
        classifier = pipeline.named_steps["logisticregression"]
        return {**base, "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
                "coef": classifier.coef_[0].tolist(), "intercept": float(classifier.intercept_[0])}
    trees = []
    for estimator in pipeline.estimators_:
        t = estimator.tree_
        values = t.value[:, 0, :]
        positive = values[:, 1] / values.sum(axis=1)
        trees.append({"left": t.children_left.tolist(), "right": t.children_right.tolist(),
                      "feature": t.feature.tolist(), "threshold": t.threshold.tolist(),
                      "positive_probability": positive.tolist()})
    return {**base, "trees": trees}
