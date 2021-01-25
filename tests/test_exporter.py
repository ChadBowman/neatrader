import unittest
import utils
import shutil
import pandas as pd
from os.path import join
from neatrader.preprocess import EtradeImporter, CsvExporter


class TestCsvExporter(unittest.TestCase):
    def test_to_csv_quote(self):
        importer = EtradeImporter()
        exporter = CsvExporter('tests/test_data/TSLA')
        tsla = utils.fetch_resource('test_data/etrade/2020-09-09/TSLA.json')
        chain = importer.from_json(tsla)
        tsla = utils.fetch_resource('test_data/etrade/2020-09-10/TSLA.json')
        chain2 = importer.from_json(tsla)
        try:
            base = exporter.to_csv(chain)
            base = exporter.to_csv(chain2)

            df = pd.read_csv(join(base, 'close.csv'))
            self.assertEqual(200909, df['date'][0])
            self.assertEqual(366.28, df['close'][0])
            self.assertEqual(200910, df['date'][1])
        finally:
            shutil.rmtree(base)

    def test_to_csv_chain(self):
        importer = EtradeImporter()
        exporter = CsvExporter('tests')
        tsla = utils.fetch_resource('test_data/etrade/2020-09-09/TSLA.json')
        chain = importer.from_json(tsla)
        try:
            base = exporter.to_csv(chain)

            df = pd.read_csv(join(base, 'chains', '200909.csv'))
            self.assertEqual(20.0, df['strike'][0])
            self.assertEqual(8386, len(df))
        finally:
            shutil.rmtree(base)
