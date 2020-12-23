import pandas as pd


def min_max(cols):
    mn = cols.min().min()
    mx = cols.max().max()
    return cols.apply(lambda x: (x - mn) / (mx - mn))


class Normalizer:
    def __init__(self, path):
        self.path = path

    def normalize_ta(self):
        # TODO define scale by configuration to allow for future prices that are above the current max
        df = pd.read_csv(self.path / 'ta.csv', parse_dates=['date'])
        self._replace_cols(df, ['close', 'bb_bbm', 'bb_bbh', 'bb_bbl'], min_max)
        self._replace_cols(df, ['macd', 'macd_signal', 'macd_diff'], min_max)
        self._replace_cols(df, ['rsi'], lambda x: x / 100)
        return df

    def to_csv(self, out_path=None):
        path = out_path if out_path else self.path / 'norm_ta.csv'
        self.ta().to_csv(path, encoding='utf-8')

    def _replace_cols(self, df, cols, func):
        df[cols] = func(df[cols])
