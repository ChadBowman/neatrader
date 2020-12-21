import pandas as pd
from ta.utils import dropna
from ta.trend import MACD
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator


class TechnicalAnalysis:
    def __init__(self, source_file):
        self.source_file = source_file

    def generate(self):
        df = pd.read_csv(self.source_file, sep=',', header=None, skiprows=1, usecols=[1])
        df = dropna(df)
        close = df[1]
        self._macd(df, close)
        self._bollinger_bands(df, close)
        self._rsi(df, close)
        return df

    def _macd(self, df, close):
        macd = MACD(close=close)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()

    def _bollinger_bands(self, df, close):
        bb = BollingerBands(close=close)
        df['bb_bbm'] = bb.bollinger_mavg()
        df['bb_bbh'] = bb.bollinger_hband()
        df['bb_bbl'] = bb.bollinger_lband()

    def _rsi(self, df, close):
        rsi = RSIIndicator(close=close)
        df['rsi'] = rsi.rsi()
