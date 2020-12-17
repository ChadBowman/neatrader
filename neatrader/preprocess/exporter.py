import csv
import os.path
from neatrader.utils import flatten_dict


class CsvExporter:
    def __init__(self, path=''):
        self.path = path

    def to_csv(self, chain):
        """ Appends chain to file if exists """
        security = chain.security
        date = chain.date.strftime('%y%m%d')
        file_name = os.path.join(self.path, f"chains_{security.symbol}.csv")
        append = os.path.exists(file_name)
        mode = 'a' if append else 'w'

        with open(file_name, mode, encoding='utf-8') as f:
            writer = csv.writer(f)
            contracts = self._to_list(chain)
            if not append:
                writer.writerow(['date', 'quote', 'expiration type strike price delta theta'])
            writer.writerow([date, chain.security.last_quote()] + contracts)
        return file_name

    def _to_list(self, chain):
        return [self._csv_field(c) for c in flatten_dict(chain.chain)]

    def _csv_field(self, contract):
        date = contract.expiration.strftime('%y%m%d')
        return f"{date} {contract.type[0]} {contract.strike} {contract.price} {contract.delta} {contract.theta}"
