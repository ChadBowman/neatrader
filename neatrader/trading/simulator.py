import numpy as np
import pandas as pd
from neatrader.trading import TradingEngine, StockSplitHandler
from neatrader.preprocess import CsvImporter
from neatrader.utils import small_date
from neatrader.math import un_min_max, min_max
from datetime import timedelta


class Simulator:
    def __init__(self, security, portfolio, path, training, reporter=None):
        self.security = security
        self.portfolio = portfolio
        self.path = path
        self.training = training
        self.reporter = reporter
        self.scales = pd.read_csv(path / 'scales.csv', index_col=0)
        self.engine = TradingEngine([portfolio], reporter)
        self.split_handler = StockSplitHandler(path / 'splits.csv', security)
        self.importer = CsvImporter()

    def simulate(self, net, start=None, end=None):
        """
        runs a simulation with provided network

        net: neural network
        start: datetime to start simulation
        end: datetime to end the simulation
        """
        close = None
        for row in self._days_in_range(start, end):
            params = self._map_row(row)
            date = params[0]
            close = params[1]
            params = (
                self._normalize(self.portfolio.cash),
                self._normalize(self.portfolio.stocks()[self.security]),
                *params[1::]  # shave off date
            )
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

    def _most_recent_chain(self, date):
        """
        Iterates in reverse for each day until the most recent options chain is discovered

        TODO: use memoization to avoid recreateing this large object
        """
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
        mask = (self.training['date'] > start) & (self.training['date'] <= end)
        for idx, row in self.training.loc[mask].iterrows():
            yield row

    def _map_row(self, row):
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
                    if self.reporter:
                        self.reporter.record(date, 'buy', contract, new_price)
                except Exception as e:
                    print(e)

    def _sell(self, date, close, delta, theta):
        # for now, limit agent to only one short contract
        if not self.portfolio.contracts():
            chain = self._most_recent_chain(date)
            # sell a new contract
            contract = chain.search(self._denormalize(close), delta=delta, theta=theta)
            try:
                self.engine.sell_contract(self.portfolio, contract, contract.price)
                if self.reporter:
                    self.reporter.record(date, 'sell', contract, contract.price)
            except Exception as e:
                print(e)

    def _denormalize(self, x):
        mn = self.scales.loc['close', 'min']
        mx = self.scales.loc['close', 'max']
        return un_min_max(x, mn, mx)

    def _normalize(self, x):
        mn = self.scales.loc['close', 'min']
        mx = self.scales.loc['close', 'max']
        return min_max(x, mn, mx)
