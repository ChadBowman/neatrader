import pandas as pd
from neatrader.utils import from_small_date
from ta.utils import dropna
from ta.trend import MACD
from ta.volatility import BollingerBands
from ta.momentum import RSIIndicator


class TechnicalAnalysis:
    def __init__(self, source_path):
        self.source_path = source_path

    def generate(self):
        df = pd.read_csv(self.source_path / 'close.csv', parse_dates=['date'], date_parser=from_small_date)
        df = dropna(df)
        close = df['close']
        self._macd(df, close)
        self._bollinger_bands(df, close)
        self._rsi(df, close)
        return df

    def to_csv(self, out_path=None):
        file_path = out_path if out_path else self.source_path / 'ta.csv'
        df = self.generate()
        df.to_csv(file_path, encoding='utf-8', index=False)
        return file_path

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