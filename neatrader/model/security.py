
class Security:
    """ A stock market security. Usually a stock or ETF. """
    def __init__(self, symbol):
        self.symbol = symbol

    def __str__(self):
        return self.symbol

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.symbol == other.symbol

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.symbol)


class Quote:
    """ A single security quote """
    def __init__(self, quote, datetime):
        self.quote = quote
        self.datetime = datetime

    def __repr__(self):
        return str(self.quote)

    def __lt__(self, other):
        return self.datetime < other.datetime

    def __gt__(self, other):
        return self.datetime > other.datetime

    def __eq__(self, other):
        return self.datetime == other.datetime
