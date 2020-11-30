
class Security:
    """ A stock market security. Usually a stock or ETF. """
    def __init__(self, symbol):
        self.symbol = symbol
        self.quotes = {}

    def __str__(self):
        return self.symbol

    def __repr__(self):
        return str(self)

    def add_quote(self, quote):
        self.quotes[quote.date] = quote

    def last_quote(self):
        if not self.quotes:
            return None
        return self.quotes[sorted(self.quotes)[0]]


class Quote:
    """ A single security quote """
    def __init__(self, close, date):
        self.close = close
        self.date = date
