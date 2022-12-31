import os
import pandas as pd
import unittest
from neatrader.preprocess import TrainingSetGenerator
from pathlib import Path


class TestTraningSetGenerator(unittest.TestCase):
    def test_generate(self):
        ta = TrainingSetGenerator(Path("tests/test_data/TSLA"))
        df = ta.generate()
        self.assertAlmostEqual(df["macd"][30], 152.782, places=3)

    def test_to_csv(self):
        ta = TrainingSetGenerator(Path("tests/test_data/TSLA"))
        try:
            path = ta.to_csv(Path("tests"), cv_proportion=0.2)

            tr = pd.read_csv(path / "training.csv")
            cv = pd.read_csv(path / "cross_validation.csv")

            self.assertEqual(len(tr), 60)
            self.assertEqual(len(cv), 15)
        finally:
            os.remove("tests/training.csv")
            os.remove("tests/cross_validation.csv")
