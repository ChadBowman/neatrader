import json
import re
from datetime import datetime
from neatrader.model import Security, Quote, Option, OptionChain


class EtradeImporter:
    def from_json(self, file_name):
        with open(file_name, 'r') as f:
            chain_json = json.load(f)
            security = Security(chain_json['quote']['symbol'])
            match = re.match(r"\d+:\d+:\d+ E.T (\d+-\d+-\d+)", chain_json['quote']['dateTime'])
            date = datetime.strptime(match.group(1), '%m-%d-%Y')
            quote = self._parse_quote(date, chain_json['quote'])
            security.add_quote(quote)
            del chain_json['quote']
            return self._parse_option_chain(security, date, chain_json)

    def _parse_quote(self, date, json):
        return Quote(json['lastTrade'], date)

    def _parse_option_chain(self, security, date, json):
        chain = OptionChain(security, date)
        for exp_dt, options in json.items():
            for option in options:
                chain.add_option(self._parse_option(security, exp_dt, option))
        return chain

    def _parse_option(self, security, exp_dt, json):
        type = json['optionType'].lower()
        strike = json['strikePrice']
        expiration = datetime.strptime(exp_dt, '%Y-%m-%d')
        option = Option(type, security, strike, expiration)
        option.delta = json['OptionGreeks']['delta']
        option.theta = json['OptionGreeks']['theta']
        option.vega = json['OptionGreeks']['vega']
        option.iv = json['OptionGreeks']['iv']
        option.price = json['lastPrice']
        return option
