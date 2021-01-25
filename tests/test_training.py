import unittest
import os
import pandas as pd
from pathlib import Path
from neatrader.preprocess import TrainingSetGenerator


class TestTraningSetGenerator(unittest.TestCase):
    def test_generate(self):
        ta = TrainingSetGenerator(Path('tests/test_data/TSLA'))
        df = ta.generate()
        self.assertAlmostEqual(df['macd'][30], 154.01, places=3)

    def test_to_csv(self):
        ta = TrainingSetGenerator(Path('tests/test_data/TSLA'))
        try:
            path = ta.to_csv(Path('tests'), cv_proportion=0.2)

            tr = pd.read_csv(path / 'training.csv')
            cv = pd.read_csv(path / 'cross_validation.csv')

            self.assertEqual(len(tr), 61)
            self.assertEqual(len(cv), 16)
        finally:
            os.remove('tests/training.csv')
            os.remove('tests/cross_validation.csv')
