import logging
import math
import pandas as pd
from functools import lru_cache
from itertools import chain
from neatrader.utils import flatten_dict, add_value, small_date
from pandas import Timestamp
from datetime import datetime

log = logging.getLogger(__name__)


class Option:
    """ A stock option """
    CALL = "call"
    PUT = "put"

    def __init__(self, direction, security, strike, expiration):
        self.direction = direction
        self.security = security
        self.strike = strike
        # TODO probably not the best way to deal with this
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
            ))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.direction, self.security, self.strike, self.expiration))

    def expired(self, now):
        return self.expiration.date() <= now.date()

    def intrinsic(self, price_underlying):
        if self.direction == Option.CALL:
            return max(price_underlying - self.strike, 0)
        else:
            return max(self.strike - price_underlying, 0)

    def extrinsic(self, price_underlying):
        if self.price is None:
            raise Exception("cannot calculate extrinsic value for option: {self}, missing price")
        return self.price - self.intrinsic(price_underlying)

    def itm(self, price_underlying):
        if self.direction == Option.CALL:
            return price_underlying > self.strike
        else:
            return price_underlying < self.strike


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
        result = None
        callput = self.chain.get(direction)
        if callput:
            exp = callput.get(expiration)
            if exp:
                result = exp.get(strike)
        if result is None:
            log.warn(f"{direction}, {expiration}, {strike} option not found in chain {self}")
        return result

    def search(self, close, *, theta, delta):
        """ Search for an option contract for a given theta and delta.

            First finds the expiration matching the closest theta,
            then finds the contract with the closest delta.

            O(n^3) due to _expirations_by_price_weighed_theta() being O(n^2)
            and having to iterate on entire result.
        """
        direction = "call"  # 'put' if delta < 0 else 'call' TODO support for puts
        exp = None
        best_theta_error = math.inf
        agg_thetas = self._expirations_by_price_weighted_theta(direction, close)
        # agg_thetas should already be sorted and we could use binary search
        # but this wont be more than about 20 elements
        for expiration, agg_theta in agg_thetas.items():
            theta_error = abs(agg_theta - theta) ** 2
            if theta_error < best_theta_error:
                exp = expiration
                best_theta_error = theta_error

        if exp is None:
            raise Exception(f"No expiration could be chosen for option search, ",
                            "theta: {theta}, agg_thetas: {agg_thetas}")

        contracts = self.chain[direction][exp]
        # These should be nearly sorted already, but just in case
        contracts = sorted(contracts.values(), key=lambda contract: contract.delta, reverse=True)
        i, j = 0, len(contracts) - 1
        while i <= j:
            mid = i + (j-i) // 2
            prospect_delta = contracts[mid].delta
            mid_error = abs(delta - prospect_delta) ** 2
            left_error = abs(delta - contracts[max(mid-1, 0)].delta) ** 2
            right_error = abs(delta - contracts[min(mid+1, len(contracts)-1)].delta) ** 2

            if mid_error <= left_error and mid_error <= right_error:
                # closest delta found, return contract
                return contracts[mid]

            if delta > prospect_delta:
                j = mid - 1
            else:
                i = mid + 1
        raise Exception(f"Unable to find contract close to delta: {delta}, ",
                        "contracts: {contracts}")

    @lru_cache(maxsize=None)
    def get_price(self, contract):
        option = self.get_option(contract.direction, contract.expiration, contract.strike)
        if option is None:
            log.warn(f"could not locate {contract} to provide a price")
        return option.price if option else 0

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

    @lru_cache(maxsize=None)
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

    @lru_cache(maxsize=None)
    def _expirations_by_price_weighted_theta(self, direction, close):
        """
        Calculates an average, price-weighted theta for each expiration (calls or puts)
        so an expiration date can be determined (searched for) by a given theta.

        For each expiration, iterates through each contract selects for OTM and present theta.
        Only out-of-the-money contracts are used since they are 100% extrinsic value.
        Returns: dict of expiration: average, price-weighted theta.
        O(n^2) all puts or calls * each strike
        """
        contracts = self.calls() if direction == 'call' else self.puts()
        result = {}
        for expiration, strike_list in contracts.items():
            weighted_theta_agg = 0
            price_total = 0
            for strike, contract in strike_list.items():
                if not contract.itm(close) and not math.isnan(contract.theta) and contract.price > 0:
                    weighted_theta_agg += contract.price * contract.theta
                    price_total += contract.price
            if price_total != 0:
                result[expiration] = weighted_theta_agg / price_total
        return result
