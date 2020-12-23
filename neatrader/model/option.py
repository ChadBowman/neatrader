import pandas as pd
from itertools import chain
from neatrader.utils import flatten_dict, add_value, small_date


class Option:
    """ A stock option """
    def __init__(self, direction, security, strike, expiration):
        self.direction = direction
        self.security = security
        self.strike = strike
        self.expiration = expiration

    def __str__(self):
        date = self.expiration.strftime("%Y-%m-%d")
        return f"{self.security} ${self.strike} {self.direction.upper()} {date}"

    def __repr__(self):
        return str(self)


class OptionChain:
    """ A collection of available options for a single security """
    def __init__(self, security, date):
        # keyed by date
        self.chain = {
            'call': {},
            'put': {}
        }
        self.security = security
        self.date = date

    def __str__(self):
        date = self.date.strftime("%Y%m%d")
        return f"{self.security.symbol}{date}"

    def add_option(self, option):
        """example:
            call: {
                2020-04-20: {
                    $420: option
                }
            }
        """
        exp_dict = self.chain[option.direction].get(option.expiration, {})
        exp_dict[option.strike] = option
        self.chain[option.direction][option.expiration] = exp_dict

    def get_option(self, direction, expiration, strike):
        return self.chain[direction][expiration][strike]

    def search(self, *, theta, delta):
        """ finds an option that has the closest theta and delta.
            The closest option is the one with the smallest sum of the squared difference
            of both theta and delta.
        """
        direction = 'call' if delta > 0 else 'put'
        error = 100
        best = None
        for strikes in self.chain[direction].values():
            for option in strikes.values():
                new_error = (theta - option.theta) ** 2 + (delta - option.delta) ** 2
                if new_error < error:
                    best = option
                    error = new_error
        return best

    def calls(self):
        return self.chain['call']

    def puts(self):
        return self.chain['put']

    def otm(self, expiration):
        """ finds all out of the money option contracts
            for a particular expiration date.
        """
        underlying = self.security.last_quote().close
        otm_calls = []
        for strike, contract in self.calls()[expiration].items():
            if strike > underlying:
                otm_calls.append(contract)
        otm_puts = []
        for strike, contract in self.puts()[expiration].items():
            if strike < underlying:
                otm_puts.append(contract)
        return {
            'call': otm_calls,
            'put': otm_puts
        }

    def iv(self, expiration):
        """ calculates the price-weighted implied volatility
            of all out of the money contracts with the same expiration.
        """
        price_total = 0
        iv = 0
        contracts = chain.from_iterable(self.otm(expiration).values())
        for contract in contracts:
            iv += contract.iv * contract.price
            price_total += contract.price
        return iv / price_total

    def to_df(self):
        contracts = {}
        for contract in flatten_dict(self.chain):
            add_value(contracts, 'direction', contract.direction)
            add_value(contracts, 'expiration', small_date(contract.expiration))
            add_value(contracts, 'strike', contract.strike)
            add_value(contracts, 'price', contract.price)
            add_value(contracts, 'iv', contract.iv)
            add_value(contracts, 'delta', contract.delta)
            add_value(contracts, 'theta', contract.theta)
            add_value(contracts, 'vega', contract.vega)
        return pd.DataFrame(contracts)
