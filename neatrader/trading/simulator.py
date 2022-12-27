import logging
import numpy as np
from datetime import timedelta
from neatrader.preprocess import CsvImporter
from neatrader.trading import TradingEngine, StockSplitHandler
from neatrader.utils import small_date

log = logging.getLogger(__name__)


class Simulator:
    chain_cache = {}

    def __init__(self, security, portfolio, path, training, reporter=None):
        self.security = security
        self.portfolio = portfolio
        self.path = path
        self.training = training
        self.reporter = reporter
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
            date, close, macd, macd_signal, macd_diff, bb_bbm, bb_bbh, bb_bbl, rsi = params
            try:
                # process assignments, expirations
                self.engine.eval({self.security: close}, date)

                cash = self.portfolio.cash  # self._normalize(self.portfolio.cash)
                shares = self.portfolio.available_shares().get(self.security, 0) / 100.0
                held_option_value = self._contract_value(date) * 100

                params = (cash, shares, held_option_value, *params[1:])

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

                    # Buy shares if 100% cash and can afford 100 shares
                    self._attempt_to_buy_shares(date, close, 100)

            except Exception as e:
                log.error(f"Failed on {self.security}:{date}")
                raise e

        return self._calculate_fitness(close, end)

    def _most_recent_chain(self, date):
        chain = Simulator.chain_cache.get(date)
        if chain is not None:
            return chain
        """
        Iterates in reverse for each day until the most recent options chain is discovered
        """
        while True:
            path = self.path / "chains" / f"{small_date(date)}.csv"
            if path.exists():
                chain = self.importer.parse_chain(date, self.security, path)
                Simulator.chain_cache[date] = chain
                return chain
            else:
                date -= timedelta(days=1)

    def _calculate_fitness(self, close, end):
        cash = self.portfolio.cash
        denorm_close = close  # self._denormalize(close)
        for contract, amt in self.portfolio.contracts().items():
            chain = self._most_recent_chain(end)
            # option prices are not normalized
            cash += chain.get_price(contract) * amt * 100
        for stock, amt in self.portfolio.stocks().items():
            cash += amt * denorm_close
        # compare against a buy-and-hold strategy
        fitness = cash - (100 * denorm_close)
        if self.reporter:
            self.reporter.fitness = fitness
        return fitness

    def _days_in_range(self, start, end):
        mask = (self.training["date"] > start) & (self.training["date"] <= end)
        for idx, row in self.training.loc[mask].iterrows():
            yield row

    def _map_row(self, row):
        date = row["date"]
        close = row["close"]
        macd = row["macd"]
        macd_signal = row["macd_signal"]
        macd_diff = row["macd_diff"]
        bb_bbm = row["bb_bbm"]
        bb_bbh = row["bb_bbh"]
        bb_bbl = row["bb_bbl"]
        rsi = row["rsi"]
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
                        self.reporter.record(date, "buy", contract, 1, new_price)
                except Exception as e:
                    log.warn(e)

    def _sell(self, date, close, delta, theta):
        # for now, limit agent to only one short contract
        if not self.portfolio.contracts():
            chain = self._most_recent_chain(date)
            # sell a new contract
            contract = chain.search(close, delta=delta, theta=theta)
            try:
                self.engine.sell_contract(self.portfolio, contract, contract.price)
                if self.reporter:
                    self.reporter.record(date, "sell", contract, -1, contract.price)
            except Exception as e:
                log.warn(e)

    def _contract_value(self, date):
        value = 0
        for contract, _ in self.portfolio.contracts().items():
            value += self._most_recent_chain(date).get_price(contract)
        return value

    def _attempt_to_buy_shares(self, date, close, num_shares):
        if not self.portfolio.has_securities():
            num_shares_afford = num_shares % int(self.portfolio.cash / close)
            if num_shares_afford == num_shares:
                self.engine.buy_shares(self.portfolio, self.security, close, num_shares_afford)
                if self.reporter:
                    self.reporter.record(date, "buy", self.security, num_shares, close)
