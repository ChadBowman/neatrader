import neatrader.preprocess as p
from neatrader.preprocess import CsvExporter
from pathlib import Path
import pandas as pd


def standardize(path, daterange):
    importer = p.EtradeImporter(Path('/Volumes/TrainingData/etrade'))
    exporter = CsvExporter(path)
    for chain in importer.for_dates('TSLA', daterange):
        if chain:
            print(f"adding {chain}")
            exporter.to_csv(chain)


def training(path):
    print("creating training/cross validation sets")
    p.TrainingSetGenerator(path / 'TSLA').to_csv()


def normalize(in_path, out_path):
    print("normalizing training sets")
    norm = p.Normalizer(in_path / 'TSLA')
    norm.to_csv(out_path / 'TSLA')


data_path = Path('data') / 'TSLA'
daterange = pd.date_range(start='2018-12-27', end='2021-01-21')
test_path = Path('tests/test_data')

#standardize(Path('data'), daterange)
#training(Path('data'))
normalize(Path('data'), Path('normalized'))
