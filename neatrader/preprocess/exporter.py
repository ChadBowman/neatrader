import csv
from neatrader.utils import flatten_dict


class CsvExporter:
    def __init__(self, path=None):
        self.path = path

    def to_csv(self, chains):
        security = chains[0].security
        file_name = f"chains_{security.symbol}.csv"
        with open(file_name, 'w', encoding='utf-8') as f:
            writer = csv.writer(f)
            for chain in chains:
                date = chain.date.strftime('%y%m%d')
                writer.writerow([date, chain.security.last_quote()] + self._to_list(chain))
        return file_name

    def _to_list(self, chain):
        return [o.csv_field() for o in flatten_dict(chain.chain)]
