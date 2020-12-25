import unittest
import utils
import pandas as pd
import math
from pathlib import Path
from datetime import datetime
from neatrader.preprocess import EtradeImporter, CsvImporter


class TestImporter(unittest.TestCase):
    def test_etrade_importer(self):
        resource = utils.fetch_resource('test_data/etrade/2020-09-09/TSLA.json')
        importer = EtradeImporter()
        chain = importer.from_json(resource)
        self.assertEqual(chain.security.symbol, 'TSLA')
        self.assertEqual(chain.security.quotes[datetime(2020, 9, 9)].date, datetime(2020, 9, 9))
        self.assertIsNotNone(chain.get_option('call', datetime(2020, 12, 18), 100))
        self.assertIsNotNone(chain.get_option('put', datetime(2020, 11, 20), 420))

        o = chain.get_option('call', datetime(2020, 12, 18), 100)
        self.assertIsNotNone(o.delta)
        self.assertIsNotNone(o.theta)
        self.assertIsNotNone(o.iv)
        self.assertIsNotNone(o.price)

    def test_etrade_for_dates(self):
        importer = EtradeImporter(utils.test_path('test_data/etrade'))
        daterange = pd.date_range(start='2020-09-09', end='2020-09-10')
        chains = list(importer.for_dates('TSLA', daterange))
        self.assertEqual(2, len(chains))

    def test_etrade_for_dates_with_missing_file(self):
        importer = EtradeImporter(utils.test_path('test_data/etrade'))
        daterange = pd.date_range(start='2020-09-09', end='2020-12-04')
        chains = [i for i in importer.for_dates('TSLA', daterange) if i]
        self.assertEqual(2, len(chains))

    def test_etrade_for_bogus_data(self):
        importer = EtradeImporter()
        resource = utils.test_path('test_data/etrade/2020-09-09/TSLA.json')
        chain = importer.from_json(resource)
        self.assertTrue(math.isnan(chain.get_option('put', datetime(2020, 9, 11), 20).theta))

    def test_csv_importer(self):
        importer = CsvImporter()
        chain = next(importer.chains(Path('tests/test_data/TSLA')))
        self.assertEqual(chain.security.symbol, 'TSLA')
        self.assertIsNotNone(chain.get_option('call', datetime(2020, 9, 18), 420))
        self.assertEqual(datetime(2020, 1, 1), chain.security.last_quote().date)
