import pandas as pd
from os.path import split
from pathlib import Path
from neatrader.utils import from_small_date, small_date
from neatrader.math import min_max


class Normalizer:
    def __init__(self, path):
        self.path = path
        self.scales = self._compute_scales()

    def normalize_training(self):
        return self._normalize_set(self.path / 'training.csv')

    def normalize_cv(self):
        return self._normalize_set(self.path / 'cross_validation.csv')

    def normalize_chains(self):
        for path in (self.path / 'chains').glob('**/*.csv'):
            name = split(path)[1]
            df = pd.read_csv(path)
            for column in ['iv', 'delta', 'theta', 'vega']:
                mn, mx = self.scales.loc[column]
                df[column] = df[column].apply(lambda x: min_max(x, mn, mx))
            yield name, df

    def to_csv(self, out_path):
        training = self.normalize_training()
        training['date'] = training['date'].apply(small_date)
        training.to_csv(out_path / 'training.csv', encoding='utf-8', index=False)

        cv = self.normalize_cv()
        cv['date'] = cv['date'].apply(small_date)
        cv.to_csv(out_path / 'cross_validation.csv', encoding='utf-8', index=False)

        Path(out_path / 'chains').mkdir(exist_ok=True)
        for name, chain in self.normalize_chains():
            chain.to_csv(out_path / 'chains' / name, encoding='utf-8', index=False)

        self.scales.to_csv(out_path / 'scales.csv', encoding='utf-8')
        return out_path

    def _compute_scales(self):
        """
        combines the training set and cross validation sets,
        then records the min and max of each column
        """
        train = pd.read_csv(self.path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        cv = pd.read_csv(self.path / 'cross_validation.csv', parse_dates=['date'],
                         date_parser=from_small_date)
        df = pd.concat([train, cv], axis=0)

        # stock price group. These metrics match the security price or are very similar
        scales = {'min': {}, 'max': {}}
        stock_price = ['close', 'bb_bbm', 'bb_bbl', 'bb_bbh']
        mn, mx = self._scales_for_group(df, stock_price)
        self._add_scales_for_group(scales, stock_price, mn, mx)

        # macd is on it's own scale
        macd = ['macd', 'macd_signal', 'macd_diff']
        mn, mx = self._scales_for_group(df, macd)
        self._add_scales_for_group(scales, macd, mn, mx)

        # option greeks are on their own scale
        greeks = ['iv', 'delta', 'theta', 'vega']
        mins = []
        maxs = []
        for path in (self.path / 'chains').glob('**/*.csv'):
            df = pd.read_csv(path, usecols=greeks)
            mn, mx = self._scales_for_group(df, greeks)
            mins.append(mn)
            maxs.append(mx)
        self._add_scales_for_group(scales, greeks, min(mins), max(maxs))

        return pd.DataFrame(data=scales)

    def _add_scales_for_group(self, scales, group, mn, mx):
        scales['min'] = {**scales['min'], **{label: mn for label in group}}
        scales['max'] = {**scales['max'], **{label: mx for label in group}}

    def _scales_for_group(self, df, columns):
        group = df[columns]
        mn = group.min().min()
        mx = group.max().max()
        return (mn, mx)

    def _normalize_set(self, path):
        df = pd.read_csv(path, parse_dates=['date'], date_parser=from_small_date)
        for col in df.columns:
            if col in self.scales.index:
                mn = self.scales['min'][col]
                mx = self.scales['max'][col]
                df[col] = df[col].apply(lambda x: min_max(x, mn, mx))
        df['rsi'] = df['rsi'].apply(lambda x: x / 100)
        return df
