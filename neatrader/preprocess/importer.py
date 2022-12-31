import json
import numpy as np
import pandas as pd
import re
from datetime import datetime
from neatrader.model import Security, Quote, OptionChain, Option
from neatrader.quote_service import QuoteService
from neatrader.utils import from_small_date
from pathlib import Path


class EtradeImporter:
    def __init__(self, path=None, quote_service=None):
        self.path = path
        self.quote_service = quote_service or QuoteService()

    def for_dates(self, symbol, date_range):
        """
        Imports multiple option chains and quotes for a single security.

        directory: location of root directory
        symbol: symbol of security
        date_range: a pandas date_range
        """
        security = None
        for date in date_range:
            path = self.path / str(date.date()) / f"{symbol}.json"
            chain = self.from_json(path, security)
            yield chain
            security = chain.security if chain else None

    def from_json(self, file_name, security=None):
        try:
            with open(file_name, "r") as f:
                chain_json = json.load(f)
                date = self._parse_date(file_name)
                quote = self._parse_quote(date, chain_json["quote"])
                if not security:
                    security = Security(chain_json["quote"]["symbol"])
                self.quote_service.add_quote(security, quote)
                del chain_json["quote"]
                return self._parse_option_chain(security, date, chain_json)
        except FileNotFoundError:
            return None

    def _parse_quote(self, date, json):
        return Quote(json["lastTrade"], date)

    def _parse_option_chain(self, security, date, json):
        chain = OptionChain(security, date)
        for exp_dt, options in json.items():
            for option in options:
                chain.add_option(self._parse_option(security, exp_dt, option))
        return chain

    def _parse_option(self, security, exp_dt, json):
        direction = json["optionType"].lower()
        strike = json["strikePrice"]
        expiration = datetime.strptime(exp_dt, "%Y-%m-%d")
        option = Option(direction, security, strike, expiration)
        option.delta = self._scrub_value(json["OptionGreeks"]["delta"])
        option.theta = self._scrub_value(json["OptionGreeks"]["theta"])
        option.vega = self._scrub_value(json["OptionGreeks"]["vega"])
        option.iv = self._scrub_value(json["OptionGreeks"]["iv"])
        option.price = self._scrub_value(json["lastPrice"])
        return option

    def _parse_date(self, file_name):
        p = Path(file_name)
        match = re.match(r".*/(\d+-\d+-\d+)", str(p.parent))
        return datetime.strptime(match.group(1), "%Y-%m-%d")

    def _scrub_value(self, value):
        return np.nan if value == -9999999.0 else value


class CsvImporter:
    def chains(self, path):
        """ imports chain data from a pathlib.Path """
        symbol = path.name
        security = Security(symbol)
        for f in path.glob("chains/*.csv"):
            date = from_small_date(f.name.replace(".csv", ""))
            yield self.parse_chain(date, security, f)

    def parse_quotes(self, path):
        df = pd.read_csv(path, parse_dates=["date"], date_parser=from_small_date)
        for index, quote in df.iterrows():
            yield Quote(quote["close"], quote["date"].to_pydatetime())

    def parse_chain(self, date, security, path):
        chain = OptionChain(security, date)
        df = pd.read_csv(path, parse_dates=["expiration"], date_parser=from_small_date)
        for index, contract in df.iterrows():
            expiration = contract["expiration"].to_pydatetime()
            direction = contract["direction"]
            strike = contract["strike"]
            option = Option(direction, security, strike, expiration)
            option.price = contract["price"]
            option.delta = contract["delta"]
            option.theta = contract["theta"]
            option.vega = contract["vega"]
            option.iv = contract["iv"]
            chain.add_option(option)
        return chain
