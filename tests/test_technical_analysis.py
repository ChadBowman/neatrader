import unittest
import test_utils
from neatrader.preprocess import TechnicalAnalysis


class TestTechnicalAnalysis(unittest.TestCase):
    def test_generate(self):
        chains = test_utils.fetch_resource('test_chains_TSLA.csv')
        ta = TechnicalAnalysis(chains)
        df = ta.generate()
        assert 10 < len(df['macd'])
        assert 10 < len(df['bb_bbm'])
        assert 10 < len(df['rsi'])
