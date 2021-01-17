
class Security:
    """ A stock market security. Usually a stock or ETF. """
    def __init__(self, symbol):
        self.symbol = symbol
        self.quotes = {}  # TODO this has caused a lot of issues and
        # im not sure it should even be apart of Security

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

    def add_quote(self, quote):
        self.quotes = {quote.date: quote}

    def last_quote(self):
        return next(iter(self.quotes.values()))  # TODO change this


class Quote:
    """ A single security quote """
    def __init__(self, close, date):
        self.close = close
        self.date = date

    def __repr__(self):
        return str(self.close)
