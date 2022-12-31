import neatrader.preprocess as p
import pandas as pd
from neatrader.preprocess import CsvExporter
from pathlib import Path


def standardize(path, daterange):
    importer = p.EtradeImporter(Path("/Volumes/TrainingData/etrade"))
    exporter = CsvExporter(path)
    for chain in importer.for_dates("TSLA", daterange):
        if chain:
            print(f"adding {chain}")
            exporter.to_csv(chain)


def add_iv(path):
    importer = p.CsvImporter()
    exporter = p.CsvExporter(path)
    quotes = {quote.datetime: quote for quote in importer.parse_quotes(path / "TSLA" / "close.csv")}

    for chain in importer.chains(path / "TSLA"):
        quote = quotes[chain.date]
        iv = {}
        for days_future in [10, 20, 30, 60, 90]:
            expiration = chain.closest_expiration(days_future)
            iv[f"iv_{days_future}"] = chain.iv(expiration, quote.quote)
        exporter.append_close("TSLA", quote, iv)


def training(path):
    print("creating training/cross validation sets")
    p.TrainingSetGenerator(path / "TSLA").to_csv()


def normalize(in_path, out_path):
    print("normalizing training sets")
    norm = p.Normalizer(in_path / "TSLA")
    norm.to_csv(out_path / "TSLA")


data_path = Path("data") / "TSLA"
daterange = pd.date_range(start="2018-12-27", end="2021-01-21")
test_path = Path("tests/test_data")

#standardize(Path("data"), daterange)

if __name__ == "__main__":
    #add_iv(Path("tests/test_data"))
    #training(Path("tests/test_data"))
    #normalize(Path("tests/test_data"), Path("tests/test_data/normalized"))
