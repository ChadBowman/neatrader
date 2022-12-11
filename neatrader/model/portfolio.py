from neatrader.model import Option, Security


class Portfolio:
    def __init__(self, cash=0, securities=None):
        self.cash = cash
        self.securities = {} if securities is None else securities
        self.collateral = {}

    def __str__(self):
        return f"cash: {self.cash}\nsecurities: {self.securities}\ncollateral: {self.collateral}"

    def contracts(self):
        return {contract: amt for contract, amt in self.securities.items() if isinstance(contract, Option)}

    def stocks(self):
        return {security: amt for security, amt in self.securities.items() if isinstance(security, Security)}
