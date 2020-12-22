import unittest
import utils
import pandas as pd
from datetime import datetime
from neatrader.preprocess import EtradeImporter, CsvImporter


class TestImporter(unittest.TestCase):
    def test_chain_importer(self):
        resource = utils.fetch_resource('2020-09-09/TSLA.json')
        importer = EtradeImporter()
        chain = importer.from_json(resource)

        assert chain.security.symbol == 'TSLA'
        assert chain.security.quotes[datetime(2020, 9, 9)].date == datetime(2020, 9, 9)
        assert chain.get_option('call', datetime(2020, 12, 18), 100) is not None
        assert chain.get_option('put', datetime(2020, 11, 20), 420) is not None

        o = chain.get_option('call', datetime(2020, 12, 18), 100)
        assert o.delta is not None
        assert o.theta is not None
        assert o.iv is not None
        assert o.price is not None

    def test_for_dates(self):
        importer = EtradeImporter()
        daterange = pd.date_range(start='2020-09-09', end='2020-09-10')
        root = utils.fetch_resource()
        chains = list(importer.for_dates(root, 'TSLA', daterange))
        assert 2 == len(chains)

    def test_for_dates_with_missing_file(self):
        importer = EtradeImporter()
        daterange = pd.date_range(start='2020-09-09', end='2020-12-04')
        root = utils.fetch_resource()
        chains = [i for i in importer.for_dates(root, 'TSLA', daterange) if i]
        assert 2 == len(chains)

    def test_csv_importer(self):
        resource = utils.fetch_resource('test_chains_TSLA.csv')
        importer = CsvImporter()
        chain = next(importer.chains(resource))
        assert chain.security.symbol == 'TSLA'
        assert chain.get_option('call', datetime(2020, 9, 18), 420) is not None
