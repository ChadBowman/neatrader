

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
                            if amt < 0:
                                print(f"assign: {contract}")
                                self.assign(portfolio, contract, amt)
                            elif amt > 0:
                                print('exercise')
                                self.exercise(portfolio, contract, amt)
                        else:
                            print('expire')
                            self.expire(portfolio, contract, amt)

    def expire(self, portfolio, contract, amt):
        if amt < 0:
            portfolio.collateral[contract.security] += amt * 100
        del portfolio.securities[contract]

    def assign(self, portfolio, contract, amt):
        """assign short option contract"""
        if contract.direction == 'call':
            shares = portfolio.securities.get(contract.security, 0)
            if shares < 100 * abs(amt):
                raise Exception(f"not enough shares to assign call. shares: {shares}, call: {contract}, amt: {amt}")
            # call away shares
            portfolio.securities[contract.security] = shares + (100 * amt)
            # update cash
            portfolio.cash += contract.strike * 100 * abs(amt)

        if contract.direction == 'put':
            cash = portfolio.cash
            if cash < contract.strike * 100 * abs(amt):
                raise Exception(f"not enough cash to to assign put. cash: {cash}, put: {contract}, amt: {amt}")
            # update cash
            portfolio.cash = cash - contract.strike * 100 * abs(amt)
            # put shares
            securities = portfolio.securities.get(contract.security, 0)
            portfolio.securities[contract.security] = securities + (100 * abs(amt))

        # reduce contracts
        portfolio.securities[contract] -= amt
        # reduce collateral
        self._reduce_collateral(portfolio, contract, amt)

    def exercise(self, portfolio, contract, amt):
        cash = portfolio.cash
        shares = portfolio.securities.get(contract.security, 0)

        if contract.direction == 'call':
            if cash < contract.strike * 100 * amt:
                raise Exception(f"not enough cash to exercise call. cash: {cash}, call: {contract}, amt: {amt}")
            # reduce cash
            portfolio.cash -= contract.strike * 100 * amt
            # add shares
            portfolio.securities[contract.security] = shares + (100 * amt)

        if contract.direction == 'put':
            if shares < 100 * amt:
                raise Exception(f"not enough shares to exercise put. shares: {shares}, put: {contract}, amt: {amt}")
            # reduce shares
            portfolio.securities[contract.security] -= 100 * amt
            # add cash
            portfolio.cash += contract.strike * 100 * amt

        # reduce contracts
        portfolio.securities[contract] -= amt

    def buy_contract(self, portfolio, contract, price, amt=1):
        if portfolio.cash < price * 100:
            raise Exception(f"not enough cash to buy {contract} for ${price}. cash: {portfolio.cash}")

        self._reduce_collateral(portfolio, contract, amt)
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

    def _reduce_collateral(self, portfolio, contract, amt):
        # release collateral if needed
        collateral = portfolio.collateral.get(contract.security, 0)
        adjusted_coll = collateral - (100 * abs(amt))
        if adjusted_coll >= 0:
            portfolio.collateral[contract.security] = adjusted_coll
        else:
            portfolio.collateral[contract.security] = 0
