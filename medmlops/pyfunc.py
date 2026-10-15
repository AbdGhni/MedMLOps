"""MLflow pyfunc flavor loading only a bounded numeric JSON model."""
import json
from pathlib import Path

from .candidate_validation import validate_structure
from .datasets import FEATURES
from .scoring import predict


class NumericModel:
    def __init__(self, path):
        self.bundle = json.loads(Path(path).read_text())
        validate_structure(self.bundle)

    def predict(self, frame, params=None):
        if list(frame.columns) != list(FEATURES):
            raise ValueError('MLflow feature order mismatch')
        return predict(self.bundle, frame.to_numpy(dtype=float))


def _load_pyfunc(data_path):
    return NumericModel(data_path)
