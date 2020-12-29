import pandas as pd
from os.path import split
from pathlib import Path


class Normalizer:
    GREEKS = ['iv', 'theta', 'vega']

    def __init__(self, path):
        self.path = path
        self.scales = pd.DataFrame(data={'min': [], 'max': []})

    def normalize_ta(self):
        df = pd.read_csv(self.path / 'ta.csv', parse_dates=['date'])
        self._replace_cols(df, ['close', 'bb_bbm', 'bb_bbh', 'bb_bbl'], self._min_max)
        self._replace_cols(df, ['macd', 'macd_signal', 'macd_diff'], self._min_max)
        self._replace_cols(df, ['rsi'], lambda x: x / 100)
        return df

    def normalize_chains(self):
        self.scales = pd.concat([self.scales, self._compute_chain_scales()])
        for path in (self.path / 'chains').glob('**/*.csv'):
            name = split(path)[1]
            df = pd.read_csv(path)
            for column in Normalizer.GREEKS:
                mn, mx = self.scales.loc[column]
                self._replace_cols(df, column, lambda x: (x - mn) / (mx - mn))
            yield name, df

    def to_csv(self, out_path):
        self.normalize_ta().to_csv(out_path / 'ta.csv', encoding='utf-8', index=False)
        Path(out_path / 'chains').mkdir(exist_ok=True)
        for name, chain in self.normalize_chains():
            chain.to_csv(out_path / 'chains' / name, encoding='utf-8', index=False)
        self.scales.to_csv(out_path / 'scales.csv', encoding='utf-8')

    def _replace_cols(self, df, cols, func):
        df[cols] = func(df[cols])

    def _min_max(self, df):
        mn = df.min().min()
        mx = df.max().max()
        for column in df.columns:
            self.scales.loc[column] = {'min': mn, 'max': mx}
        return df.apply(lambda x: (x - mn) / (mx - mn))

    def _compute_chain_scales(self):
        mn = pd.DataFrame(data={'iv': [], 'theta': [], 'vega': []})
        mx = pd.DataFrame(data={'iv': [], 'theta': [], 'vega': []})
        for path in (self.path / 'chains').glob('**/*.csv'):
            df = pd.read_csv(path, usecols=['iv', 'theta', 'vega'])
            mn = mn.append(df.min().to_frame().T, ignore_index=True)
            mx = mx.append(df.max().to_frame().T, ignore_index=True)
        df = pd.concat([mn.min(), mx.max()], axis=1)
        df.columns = ['min', 'max']
        return df
