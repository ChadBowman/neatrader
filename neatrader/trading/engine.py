

class TradingEngine:
    def __init__(self, portfolios=[]):
        self.portfolios = portfolios

    def eval(self, prices, date):
        # check if any options have expired
        # for those that expire ITM, process assignment
        # This method becomes computationally expensive with a large amount of prices
        for portfolio in self.portfolios:
            for contract, amt in portfolio.contracts().items():
                # here security means option underlying security
                for security, price in prices.items():
                    if contract.security == security and contract.expires(date):
                        if contract.itm(price):
                            self.assign(portfolio, contract, amt)
                        else:
                            self.expire(portfolio, contract)

    def expire(self, portfolio, contract):
        del portfolio.securities[contract]

    def assign(self, portfolio, contract, amt=1):
        if contract.direction == 'call':
            shares = portfolio.securities.get(contract.security, 0)
            if shares < 100 * amt:
                raise Exception(f"not enough shares to assign call. shares: {shares}, call: {contract}, amt: {amt}")
            # call away shares
            portfolio.securities[contract.security] = shares - (100 * amt)
            # update cash
            portfolio.cash += contract.strike * 100 * amt

        if contract.direction == 'put':
            cash = portfolio.cash
            if cash < contract.strike * 100 * amt:
                raise Exception(f"not enough cash to to assign put. cash: {cash}, put: {contract}, amt: {amt}")
            # update cash
            portfolio.cash = cash - contract.strike * 100 * amt
            # put shares
            securities = portfolio.securities.get(contract.security, 0)
            portfolio.securities[contract.security] = securities + (100 * amt)

    def buy_contract(self, portfolio, contract, price, amt=1):
        if portfolio.cash < price * 100:
            raise Exception(f"not enough cash to buy {contract} for ${price}. cash: {portfolio.cash}")
        # release collateral if needed
        collateral = portfolio.collateral.get(contract.security, 0)
        adjusted_coll = collateral - (100 * amt)
        if adjusted_coll >= 0:
            portfolio.collateral[contract.security] = adjusted_coll
        else:
            portfolio.collateral[contract.security] = 0

        portfolio.cash -= price * 100 * amt
        portfolio.securities[contract] = portfolio.securities.get(contract, 0) + amt

    def sell_contract(self, portfolio, contract, price, amt=1):
        previous_contracts = portfolio.securities.get(contract, 0)
        long_contracts = previous_contracts if previous_contracts > 0 else 0

        colateral_reserved = portfolio.collateral.get(contract.security, 0)
        underlying_held = portfolio.securities.get(contract.security, 0)

        # check for available shares
        available = ((long_contracts * 100) + underlying_held) - colateral_reserved
        if available < 100 * amt:
            raise Exception(f"not enough shares available to sell {contract}. shares available: {available}, needed: {100 * amt}")

        # update contracts held
        portfolio.securities[contract] = previous_contracts - amt

        # add shares as collateral
        if amt - long_contracts > 0:
            previous_collateral = portfolio.collateral.get(contract.security, 0)
            portfolio.collateral[contract.security] = previous_collateral + (100 * (amt - long_contracts))

        # update cash
        portfolio.cash += price * 100 * amt
