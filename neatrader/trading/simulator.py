from neatrader.trading import TradingEngine, StockSplitHandler
from neatrader.preprocess import CsvImporter
from neatrader.utils import small_date, days_between
from datetime import timedelta
import random as rand
import numpy as np
import pandas as pd


class Simulator:
    def __init__(self, security, portfolio, path):
        self.security = security
        self.portfolio = portfolio
        self.path = path
        self.ta = pd.read_csv(path / 'ta.csv', parse_dates=['date'])
        self.scales = pd.read_csv(path / 'scales.csv', index_col=0)
        self.engine = TradingEngine([portfolio])
        self.split_handler = StockSplitHandler(path / 'splits.csv', security)
        self.importer = CsvImporter()
        self.training_duration = self._training_duration()

    def simulate(self, net, start=None, end=None, duration=None):
        if not start and not end and duration:
            start, end = self._random_date_range(duration)
        close = None
        for row in self._days_in_range(start, end):
            params = self._map_row(row)
            date = params[0]
            close = params[1]
            params = params[1::]  # shave off date
            try:
                # process assignments, expirations
                self.engine.eval({self.security: self._denormalize(close)}, date)

                if not np.isnan(params).any():
                    # Check for stock split and adjust portfolio accordingly
                    self.split_handler.check_and_invoke(self.portfolio, date)

                    # Activate! 🤖
                    buy, sell, hold, delta, theta = net.activate(params)

                    # Buy
                    if buy > sell and buy > hold:
                        self._buy(date)
                    # Sell
                    elif sell > buy and sell > hold:
                        self._sell(date, close, delta, theta)
            except Exception as e:
                print(f"Failed on {self.security}:{date}")
                raise e

        return self._calculate_fitness(close, end)

    def _training_duration(self):
        mn = min(self.ta['date'])
        mx = max(self.ta['date'])
        return days_between(mn, mx)

    def _date_range_by_end_target(self, duration, end_target):
        """
        Returns a date range (start, end) that that ensures an end date
        that is a trading day with a closing price and includes duration
        amount of calendar days in the range. The start date is not guarenteed
        to be a trading day or have a closing price.
        """
        i = round(end_target / self.training_duration * len(self.ta)-1)
        end = self.ta.loc[i, 'date']
        start = end - timedelta(days=duration)
        return (start, end)

    def _random_date_range(self, duration):
        end_date_target = rand.randint(duration, self.training_duration)
        return self._date_range_by_end_target(duration, end_date_target)

    def _most_recent_chain(self, date):
        while True:
            path = self.path / 'chains' / f"{small_date(date)}.csv"
            if path.exists():
                return self.importer.parse_chain(date, self.security, path)
            else:
                date -= timedelta(days=1)

    def _calculate_fitness(self, close, end):
        cash = 0
        for contract, amt in self.portfolio.contracts().items():
            if amt != 0:
                chain = self._most_recent_chain(end)
                # option prices are not normalized
                cash += chain.get_price(contract) * amt * 100
        denorm_close = self._denormalize(close)
        for stock, amt in self.portfolio.stocks().items():
            cash += amt * denorm_close
        cash += self.portfolio.cash
        # compare against a buy-and-hold strategy
        return cash - (100 * denorm_close)

    def _days_in_range(self, start, end):
        mask = (self.ta['date'] > start) & (self.ta['date'] <= end)
        for idx, row in self.ta.loc[mask].iterrows():
            yield row

    def _map_row(self, row):
        # TODO add held option delta/theta, maybe vega?
        date = row['date']
        close = row['close']
        macd = row['macd']
        macd_signal = row['macd_signal']
        macd_diff = row['macd_diff']
        bb_bbm = row['bb_bbm']
        bb_bbh = row['bb_bbh']
        bb_bbl = row['bb_bbl']
        rsi = row['rsi']
        return (date, close, macd, macd_signal, macd_diff, bb_bbm, bb_bbh, bb_bbl, rsi)

    def _buy(self, date):
        # only covered calls are supported right now so this means close the position
        for contract, amt in self.portfolio.contracts().items():
            if amt < 0:
                # right now there should only be one short contract at a time
                chain = self._most_recent_chain(date)
                new_price = chain.get_price(contract)
                try:
                    self.engine.buy_contract(self.portfolio, contract, new_price)
                except Exception as e:
                    print(e)

    def _sell(self, date, close, delta, theta):
        if not self.portfolio.contracts():
            chain = self._most_recent_chain(date)
            # sell a new contract
            contract = chain.search(self._denormalize(close), delta=delta, theta=theta)
            try:
                self.engine.sell_contract(self.portfolio, contract, contract.price)
            except Exception as e:
                print(e)

    def _denormalize(self, x):
        mn = self.scales.loc['close', 'min']
        mx = self.scales.loc['close', 'max']
        return (x * (mx - mn)) + mn
