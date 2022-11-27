import pandas as pd
from neatrader.utils import small_date, from_small_date
from talib import MACD, BBANDS, RSI


class TrainingSetGenerator:
    def __init__(self, source_path):
        self.source_path = source_path

    def generate(self):
        df = pd.read_csv(self.source_path / 'close.csv', parse_dates=['date'], date_parser=from_small_date)
        df.dropna(axis=0)
        close = df['close']
        self._macd(df, close)
        self._bollinger_bands(df, close)
        self._rsi(df, close)
        return df

    def to_csv(self, out_path=None, cv_proportion=0.2):
        file_path = out_path if out_path else self.source_path
        df = self.generate()
        df['date'] = df['date'].apply(small_date)
        size = len(df)
        training_size = int(size * (1 - cv_proportion))
        df[:training_size].to_csv(file_path / 'training.csv', encoding='utf-8', index=False)
        # cross validation always uses the most recent data
        df[training_size:].to_csv(file_path / 'cross_validation.csv', encoding='utf-8', index=False)
        return file_path

    def _macd(self, df, close):
        macd = MACD(close=close)
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()

    def _bollinger_bands(self, df, close):
        bb = BBANDS(close=close)
        df['bb_bbm'] = bb.bollinger_mavg()
        df['bb_bbh'] = bb.bollinger_hband()
        df['bb_bbl'] = bb.bollinger_lband()

    def _rsi(self, df, close):
        rsi = RSI(close=close)
        df['rsi'] = rsi.rsi()
