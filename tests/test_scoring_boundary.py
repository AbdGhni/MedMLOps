import unittest

import numpy as np

from medmlops.datasets import FEATURES, SCHEMA
from medmlops.scoring import predict


class ForestBoundaryTests(unittest.TestCase):
    def test_double_threshold_is_not_rounded_to_float32(self):
        value = float(np.float32(1.0))
        threshold = value - 1e-8
        bundle = {'schema': SCHEMA, 'features': list(FEATURES), 'kind': 'forest',
                  'trees': [{'left': [1, -1, -1], 'right': [2, -1, -1],
                             'feature': [0, -2, -2], 'threshold': [threshold, -2, -2],
                             'positive_probability': [0.5, 0.0, 1.0]}]}
        matrix = np.zeros((1, len(FEATURES)))
        matrix[0, 0] = value
        self.assertEqual(predict(bundle, matrix).tolist(), [1.0])
