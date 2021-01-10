import neatrader.preprocess as p
from pathlib import Path
import pandas as pd
import shutil

importer = p.EtradeImporter(Path('/Volumes/TrainingData/etrade'))
exporter = p.CsvExporter('data')
daterange = pd.date_range(start='2020-01-01', end='2020-12-31')
norm = p.Normalizer(Path('data/TSLA'))


def standardize():
    #shutil.rmtree('data/TSLA')
    for chain in importer.for_dates('TSLA', daterange):
        if chain:
            print(f"adding {chain}")
            exporter.to_csv(chain)


def ta():
    p.TechnicalAnalysis(Path('data/TSLA')).to_csv()


def normalize():
    norm.to_csv(Path('normalized/TSLA'))


#standardize()
ta()
normalize()
