import pandas as pd
from copy import deepcopy


class StockSplitHandler:
    def __init__(self, path, security):
        self.splits = pd.read_csv(path, parse_dates=['date'], header=0)
        self.security = security

    def check_and_invoke(self, portfolio, date):
        new_stocks = {}
        for idx, row in self.splits.iterrows():
            split_date, multiplier = row
            if split_date == date:
                new_stocks = self._calculate_new_stocks(portfolio.stocks(), multiplier)
                new_contracts, to_del = self._calculate_new_contracts(portfolio.contracts(), multiplier)
                for contract in to_del:
                    del portfolio.securities[contract]
                portfolio.securities = {**portfolio.securities, **new_stocks, **new_contracts}

    def _calculate_new_stocks(self, stocks, multiplier):
        new_stocks = {}
        for stock, amt in stocks.items():
            if stock == self.security:
                new_stocks[stock] = amt * multiplier
        return new_stocks

    def _calculate_new_contracts(self, contracts, multiplier):
        new_contracts = {}
        to_del = []
        for contract, amt in contracts.items():
            if contract.security == self.security:
                contract_copy = deepcopy(contract)
                contract_copy.price = contract.price / multiplier
                contract_copy.strike = contract.strike / multiplier
                new_contracts[contract_copy] = amt * multiplier
                to_del.append(contract)
        return (new_contracts, to_del)
