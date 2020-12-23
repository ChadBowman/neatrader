import csv
import os.path
from neatrader.utils import small_date
from pathlib import Path


class CsvExporter:
    def __init__(self, path=''):
        self.path = path

    def to_csv(self, chain):
        """ Appends chain to file if exists """
        security = chain.security
        dirs = os.path.join(self.path, security.symbol)
        Path(dirs).mkdir(parents=True, exist_ok=True)

        self.append_close(security.symbol, security.last_quote())
        self.write_chain(chain)

        return dirs

    def append_close(self, symbol, quote):
        full_path = os.path.join(self.path, symbol, 'close.csv')
        append = os.path.exists(full_path)
        mode = 'a' if append else 'w'

        with open(full_path, mode, encoding='utf-8') as f:
            writer = csv.writer(f)
            if not append:
                writer.writerow(['date', 'close'])
            writer.writerow([small_date(quote.date), quote.close])

    def write_chain(self, chain):
        dirs = os.path.join(self.path, chain.security.symbol, 'chains')
        Path(dirs).mkdir(parents=True, exist_ok=True)
        path = os.path.join(dirs, f"{small_date(chain.date)}.csv")
        chain.to_df().to_csv(path, encoding='utf-8', index=False)
