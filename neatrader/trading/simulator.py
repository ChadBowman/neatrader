from neatrader.trading import TradingEngine, StockSplitHandler
from neatrader.preprocess import CsvImporter
from neatrader.utils import small_date
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

    def simulate(self, net, start, end):
        close = None
        for row in self._days_in_range(start, end):
            params = self._map_row(row)
            if not np.isnan(params[1::]).any():
                date = params[0]
                close = params[1]
                try:
                    # Check for stock split and adjust portfolio accordingly
                    self.split_handler.check_and_invoke(self.portfolio, date)

                    # Activate! 🤖
                    buy, sell, hold, delta, theta = net.activate(params[1::])

                    # HOLD BUY SELL
                    if hold > buy and hold > sell:
                        continue
                    else:
                        # This is EXTREMELY expensive!
                        chain = self._chain_for_date(date)
                        if buy > sell and buy > hold:
                            self._buy(chain)
                        else:
                            self._sell(chain, close, delta, theta)

                    # process assignments, expirations
                    self.engine.eval({self.security: self._denormalize(close)}, date)
                except Exception as e:
                    print(f"Failed on {self.security}:{date}")
                    raise e

        final_chain = self._chain_for_date(end)
        return self._calculate_fitness(close, final_chain)

    def _chain_for_date(self, date):
        return self.importer.parse_chain(
            date, self.security, self.path / 'chains' / f"{small_date(date)}.csv"
        )

    def _calculate_fitness(self, close, chain):
        cash = 0
        for contract, amt in self.portfolio.contracts().items():
            # option prices are not normalized
            cash += chain.get_price(contract) * amt * 100
        for stock, amt in self.portfolio.stocks().items():
            cash += amt * self._denormalize(close)
        cash += self.portfolio.cash
        return cash

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

    def _buy(self, chain):
        # only covered calls are supported right now so this means close the position
        if self.portfolio.contracts():
            # get the only contract
            contract = next(iter(self.portfolio.contracts().keys()))
            new_price = chain.get_price(contract)
            try:
                print(f"closing {contract}")
                self.engine.buy_contract(self.portfolio, contract, new_price)
            except Exception as e:
                print(e)

    def _sell(self, chain, close, delta, theta):
        if not self.portfolio.contracts():
            # sell a new contract
            contract = chain.search(self._denormalize(close), delta=delta, theta=theta)
            try:
                print(f"selling {contract} for ${contract.price}")
                self.engine.sell_contract(self.portfolio, contract, contract.price)
            except Exception as e:
                print(e)
                raise e

    def _denormalize(self, x):
        mn = self.scales.loc['close', 'min']
        mx = self.scales.loc['close', 'max']
        return (x * (mx - mn)) + mn
