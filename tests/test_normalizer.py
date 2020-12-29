import unittest
import math
from neatrader.preprocess import Normalizer
from pathlib import Path


class TestNormalizer(unittest.TestCase):
    def test_normalize_ta(self):
        norm = Normalizer(Path('tests/test_data/TSLA'))
        df = norm.normalize_ta()
        for i, row in df.iterrows():
            if not math.isnan(row['bb_bbh']):
                self.assertTrue(row['bb_bbh'] >= 0)
                self.assertTrue(row['bb_bbh'] <= 1)

    def test_normalize_chains(self):
        norm = Normalizer(Path('tests/test_data/TSLA'))
        name, df = next(norm.normalize_chains())
        self.assertEquals(0, len(df[df['theta'] < 0]))
        self.assertEquals('200911.csv', name)
