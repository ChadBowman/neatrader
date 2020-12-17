import sys
import pandas as pd
from neatrader.preprocess import EtradeImporter, CsvExporter


def standardize(symbol, start, end):
    print(symbol + start + end)
    importer = EtradeImporter()
    exporter = CsvExporter('data/chains/')
    date_range = pd.date_range(start=start, end=end)

    for chain in importer.for_dates('../datasets/chains', symbol, date_range):
        if chain:
            exporter.to_csv(chain)
            print(f"standaridized {chain}")


if __name__ == '__main__':
    standardize(sys.argv[1], sys.argv[2], sys.argv[3])
