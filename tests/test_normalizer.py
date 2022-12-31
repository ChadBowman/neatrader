import math
import os
import pandas as pd
import shutil
import unittest
from neatrader.preprocess import Normalizer
from pathlib import Path


class TestNormalizer(unittest.TestCase):
    def test_set_traning_scales(self):
        norm = Normalizer(Path("tests/test_data/TSLA"))

        self.assertEqual((11, 2), norm.scales.shape)
        self.assertEqual(norm.scales["min"]["close"], norm.scales["min"]["bb_bbm"])
        self.assertEqual(norm.scales["max"]["macd"], norm.scales["max"]["macd_signal"])
        self.assertNotEqual(norm.scales["min"]["close"], norm.scales["min"]["macd"])

    def test_normalize_training(self):
        norm = Normalizer(Path("tests/test_data/TSLA"))
        df = norm.normalize_training()

        self.assertEqual((60, 14), df.shape)
        for i, row in df.iterrows():
            if not math.isnan(row["bb_bbh"]):
                self.assertTrue(row["bb_bbh"] >= -1)
                self.assertTrue(row["bb_bbh"] <= 1)

    def test_normalize_cross_validation(self):
        norm = Normalizer(Path("tests/test_data/TSLA"))
        df = norm.normalize_cv()

        self.assertEqual((15, 14), df.shape)
        for i, row in df.iterrows():
            if not math.isnan(row["bb_bbh"]):
                self.assertTrue(row["bb_bbh"] >= -1)
                self.assertTrue(row["bb_bbh"] <= 1)

    def test_normalize_chains(self):
        norm = Normalizer(Path("tests/test_data/TSLA"))
        name, df = next(norm.normalize_chains())
        self.assertEquals(0, len(df[df["theta"] < -1]))
        self.assertEquals("200903.csv", name)

    def test_to_csv(self):
        norm = Normalizer(Path("tests/test_data/TSLA"))

        path = Path("tests")
        try:
            norm.to_csv(path)

            training = pd.read_csv(path / "training.csv")
            self.assertEqual((60, 14), training.shape)
            cv = pd.read_csv(path / "cross_validation.csv")
            self.assertEqual((15, 14), cv.shape)
            chain = pd.read_csv(path / "chains" / "200908.csv")
            self.assertEqual((8362, 8), chain.shape)
        finally:
            os.remove(path / "training.csv")
            os.remove(path / "cross_validation.csv")
            shutil.rmtree(path / "chains")
