from neatrader.model import Option, Security


class Portfolio:
    def __init__(self, cash=0.0, securities=None):
        self.cash = cash
        self.securities = securities or {}
        self.collateral = {}

    def __str__(self):
        return f"cash: {self.cash:.2f}\nsecurities: {self.securities}\ncollateral: {self.collateral}"

    def contracts(self):
        return {
            contract: amt for contract, amt in self.securities.items()
            if (isinstance(contract, Option)) and amt != 0
        }

    def stocks(self):
        return {
            security: amt for security, amt in self.securities.items()
            if isinstance(security, Security) and amt != 0
        }

    def available_shares(self):
        return {
            security: amt - self.collateral.get(security, 0) for security, amt in self.stocks().items()
        }
