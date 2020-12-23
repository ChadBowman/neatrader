import json
import re
import pandas as pd
from datetime import datetime
from neatrader.utils import from_small_date
from neatrader.model import Security, Quote, Option, OptionChain


class EtradeImporter:
    def for_dates(self, directory, symbol, date_range):
        """ Imports mutiple option chains and quotes for a single security.

            directory: location of root directory
            symbol: symbol of security
            date_range: a pandas date_range
        """
        security = None
        for date in date_range:
            chain = self.from_json(f"{directory}/{date.date()}/{symbol}.json", security)
            yield chain
            security = chain.security if chain else None

    def from_json(self, file_name, security=None):
        try:
            with open(file_name, 'r') as f:
                chain_json = json.load(f)
                date = self._parse_date(chain_json)
                quote = self._parse_quote(date, chain_json['quote'])
                if not security:
                    security = Security(chain_json['quote']['symbol'])
                security.add_quote(quote)
                del chain_json['quote']
                return self._parse_option_chain(security, date, chain_json)
        except FileNotFoundError:
            return None

    def _parse_quote(self, date, json):
        return Quote(json['lastTrade'], date)

    def _parse_option_chain(self, security, date, json):
        chain = OptionChain(security, date)
        for exp_dt, options in json.items():
            for option in options:
                chain.add_option(self._parse_option(security, exp_dt, option))
        return chain

    def _parse_option(self, security, exp_dt, json):
        direction = json['optionType'].lower()
        strike = json['strikePrice']
        expiration = datetime.strptime(exp_dt, '%Y-%m-%d')
        option = Option(direction, security, strike, expiration)
        option.delta = json['OptionGreeks']['delta']
        option.theta = json['OptionGreeks']['theta']
        option.vega = json['OptionGreeks']['vega']
        option.iv = json['OptionGreeks']['iv']
        option.price = json['lastPrice']
        return option

    def _parse_date(self, chain_json):
        match = re.match(r"\d+:\d+:\d+ E.T (\d+-\d+-\d+)", chain_json['quote']['dateTime'])
        return datetime.strptime(match.group(1), '%m-%d-%Y')


class CsvImporter:
    def chains(self, path):
        """ imports chain data from a pathlib.Path """
        symbol = path.name
        security = Security(symbol)
        self._parse_quotes(security, path / 'close.csv')
        for f in path.glob('chains/*.csv'):
            date = from_small_date(f.name.replace('.csv', ''))
            yield self._parse_chain(date, security, f)

    def _parse_quotes(self, security, path):
        df = pd.read_csv(path, parse_dates=['date'], date_parser=from_small_date)
        for index, quote in df.iterrows():
            quote = Quote(quote['close'], quote['date'])
            security.add_quote(quote)

    def _parse_chain(self, date, security, path):
        chain = OptionChain(security, date)
        df = pd.read_csv(path, parse_dates=['expiration'], date_parser=from_small_date)
        for index, contract in df.iterrows():
            expiration = contract['expiration']
            direction = contract['direction']
            strike = contract['strike']
            option = Option(direction, security, strike, expiration)
            option.price = contract['price']
            option.delta = contract['delta']
            option.theta = contract['theta']
            option.vega = contract['vega']
            chain.add_option(option)
        return chain
