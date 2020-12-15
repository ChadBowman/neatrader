import json
import re
import csv
from datetime import datetime
from neatrader.model import Security, Quote, Option, OptionChain


class EtradeImporter:
    def for_dates(self, location, symbol, date_range):
        for date in date_range:
            yield self.from_json(f"{location}/{date.date()}/{symbol}.json")

    def from_json(self, file_name):
        try:
            with open(file_name, 'r') as f:
                chain_json = json.load(f)
                security = Security(chain_json['quote']['symbol'])
                match = re.match(r"\d+:\d+:\d+ E.T (\d+-\d+-\d+)", chain_json['quote']['dateTime'])
                date = datetime.strptime(match.group(1), '%m-%d-%Y')
                quote = self._parse_quote(date, chain_json['quote'])
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


class CsvImporter:
    def chains(self, file_name):
        with open(file_name, 'r') as f:
            symbol = re.match(r'chains_(\w+).csv', 'chains_TSLA.csv').group(1)
            security = Security(symbol)
            for row in csv.reader(f):
                date = datetime.strptime(row[0], '%y%m%d')
                quote = row[1]
                security.add_quote(Quote(quote, date))
                chain = self._parse_chain(date, security, row[2:])
                yield chain

    def _parse_chain(self, date, security, contracts):
        chain = OptionChain(security, date)
        for contract in contracts:
            fields = contract.split(' ')
            match = re.match(r'(\d+)(c|p)(\d+\.\d*)', fields[0])
            expiration = datetime.strptime(match[1], '%y%m%d')
            direction = 'call' if match[2] == 'c' else 'put'
            strike = float(match[3])
            price = float(fields[1])
            delta = float(fields[2])
            theta = float(fields[3])
            option = Option(direction, security, strike, expiration)
            option.price = price
            option.delta = delta
            option.theta = theta
            chain.add_option(option)
        return chain
