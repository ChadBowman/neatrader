import unittest
import test_utils
from datetime import datetime
from neatrader.preprocess import EtradeImporter


class TestImporter(unittest.TestCase):
    def test_chain_importer(self):
        resource = test_utils.fetch_resource('TSLA.json')
        importer = EtradeImporter()
        chain = importer.from_json(resource)

        assert chain.security.symbol == 'TSLA'
        assert chain.security.quotes[datetime(2020, 4, 20)].date == datetime(2020, 4, 20)
        assert chain.get_option('call', datetime(2020, 4, 24), 100) is not None
        assert chain.get_option('put', datetime(2020, 5, 1), 420) is not None

        o = chain.get_option('call', datetime(2020, 4, 24), 100)
        assert o.delta is not None
        assert o.theta is not None
        assert o.iv is not None
        assert o.price is not None
