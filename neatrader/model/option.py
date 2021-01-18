import pandas as pd
import math
import datetime as datetime
from itertools import chain
from neatrader.utils import flatten_dict, add_value, small_date
from pandas import Timestamp


class Option:
    """ A stock option """
    def __init__(self, direction, security, strike, expiration):
        self.direction = direction
        self.security = security
        self.strike = strike
        # TODO probably not the best way to deal with tis
        if isinstance(expiration, Timestamp):
            expiration = expiration.to_pydatetime()
        self.expiration = expiration

    def __str__(self):
        date = self.expiration.strftime("%Y-%m-%d")
        return f"{self.security} ${self.strike} {self.direction.upper()} {date}"

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, Option):
            return all((
                self.direction == other.direction,
                self.security == other.security,
                self.strike == other.strike,
                self.expiration == other.expiration
                # TODO might need to include price here too
            ))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.direction, self.security, self.strike, self.expiration))

    def expired(self, datetime):
        return self.expiration.date() <= datetime.date()

    def itm(self, price):
        if self.direction == 'call' and price > self.strike:
            return True
        if self.direction == 'put' and price < self.strike:
            return True
        return False


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

    def search(self, close, *, theta, delta):
        """ First finds the expiration with the closest theta by
            grouping the expirations by the price-weighted theta of out of the money options,
            excluding options that expire within five days.
            Then, find the contract with the closest delta.
        """
        direction = 'put' if delta < 0 else 'call'
        exp = None
        best_theta_error = 1000
        for expiration, agg_theta in self._expirations_by_price_weighted_theta(direction, close).items():
            theta_error = abs(agg_theta - theta)
            if theta_error < best_theta_error:
                exp = expiration
                best_theta_error = theta_error

        contracts = self.chain[direction][exp]
        best = None
        best_delta_error = 2
        for strike, contract in contracts.items():
            delta_error = abs(contract.delta - delta)
            if delta_error < best_delta_error:
                best = contract
                best_delta_error = delta_error
        return best

    def get_price(self, contract):
        return self.get_option(contract.direction, contract.expiration, contract.strike).price

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

    def _expirations_by_price_weighted_theta(self, direction, close):
        if close < 1:
            raise Exception(f"denormalized closing price expected. was {close}")
        contracts = self.calls() if direction == 'call' else self.puts()
        result = {}
        five_days_future = self.date + datetime.timedelta(days=5)
        for expiration, strike_list in contracts.items():
            if expiration > five_days_future:
                weighted_theta_agg = 0
                price_total = 0
                for strike, contract in strike_list.items():
                    if not contract.itm(close) and not math.isnan(contract.theta):
                        weighted_theta_agg += contract.price * contract.theta
                        price_total += contract.price
                if price_total == 0:
                    result[expiration] = 100  # undefined
                else:
                    result[expiration] = weighted_theta_agg / price_total
        return result
