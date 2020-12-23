import unittest
import os
import pandas as pd
from pathlib import Path
from neatrader.preprocess import TechnicalAnalysis


class TestTechnicalAnalysis(unittest.TestCase):
    def test_generate(self):
        ta = TechnicalAnalysis(Path('tests/test_data/TSLA'))
        df = ta.generate()
        self.assertAlmostEqual(df['macd'][30], 84.402, places=3)

    def test_to_csv(self):
        ta = TechnicalAnalysis(Path('tests/test_data/TSLA'))
        try:
            path = ta.to_csv(Path('tests/ta.csv'))
            df = pd.read_csv(path)
            self.assertEqual(len(df), 159)
            self.assertAlmostEqual(df['macd'][30], 84.402, places=3)
        finally:
            os.remove('tests/ta.csv')
