
class TradingEngine:
    def __init__(self, portfolios=[]):
        self.portfolios = portfolios

    def eval(self, prices, date):
        # check if any options have expired
        # for those that expire ITM, process assignment
        for portfolio in self.portfolios:
            for contract in portfolio.contracts:
                for security, price in prices.items():
                    if contract.security == security and contract.expires(date) and contract.itm(price):
                        self.assign(portfolio, contract)

    def assign(self, portfolio, contract):
        if contract.direction == 'call':
            shares = portfolio.securities.get(contract.security, 0)
            if shares < 100:
                raise Exception(f"not enough shares to assign call. shares: {shares}, call: {contract}")
            # call away shares
            portfolio.securities[contract.security] = shares - 100
            # update cash
            portfolio.cash += contract.strike * 100

        if contract.direction == 'put':
            cash = portfolio.cash
            if cash < contract.strike * 100:
                raise Exception(f"not enough cash to to assign put. cash: {cash}, put: {contract}")
            # update cash
            portfolio.cash = cash - contract.strike * 100
            # put shares
            securities = portfolio.securities.get(contract.security, 0)
            portfolio.securities[contract.security] = securities + 100
