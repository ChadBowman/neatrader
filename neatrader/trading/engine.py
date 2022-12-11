class TradingEngine:
    def __init__(self, portfolios=[], reporter=None):
        self.portfolios = portfolios
        self.reporter = reporter

    def eval(self, prices, date):
        """
        check if any options have expired
        for those that expire ITM, process assignment
        This method becomes computationally expensive with a large amount of prices.
        O(n^3) theoretically, O(1) with current implementation

        prices: closing prices of underlying securities for a given date
        date: date of evaluation
        """
        for portfolio in self.portfolios:  # currently only one portfolio is used at at time
            for contract, amt in portfolio.contracts().items():  # currently an agent can only hold 1 contract at a time
                # here security means option underlying security
                for security, price in prices.items():  # currently only one security:price pair is provided
                    if contract.security == security and contract.expired(date):
                        if contract.itm(price):
                            if amt < 0:
                                self.assign(portfolio, contract, amt)
                                if self.reporter:
                                    self.reporter.record(date, 'assign', contract)
                            elif amt > 0:
                                self.exercise(portfolio, contract, amt)
                                if self.reporter:
                                    self.reporter.record(date, 'exercise', contract)
                        else:
                            self.expire(portfolio, contract, amt)
                            if self.reporter:
                                self.reporter.record(date, 'expire', contract)

    def expire(self, portfolio, contract, amt):
        """expires OTM contract, returns collateral if contract is short"""
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
        """ exercise long option contract """
        cash = portfolio.cash
        shares = portfolio.securities.get(contract.security, 0)

        if contract.direction == 'call':
            if cash < contract.strike * 100 * amt:
                raise Exception(f"not enough cash to exercise call. cash: ${cash}, call: {contract}, amt: ${amt} (* 100)")
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
            raise Exception(f"not enough cash to buy {contract} for ${price} (* 100). cash: ${portfolio.cash}")

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
