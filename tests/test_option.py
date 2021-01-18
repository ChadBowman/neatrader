import unittest
from neatrader.model import Option, Security, OptionChain, Quote
from neatrader.preprocess import CsvImporter
from datetime import datetime
from utils import TSLA
from pathlib import Path


class TestOptionChain(unittest.TestCase):
    def test_search(self):
        importer = CsvImporter()
        chain = next(importer.chains(Path('tests/test_data/TSLA')))

        result = chain.search(372.72, theta=-1.13, delta=0.3503)

        self.assertEqual(datetime(2020, 9, 25), result.expiration)
        self.assertEqual(420, result.strike)

    def test_otm(self):
        security = Security('TSLA')
        security.add_quote(Quote(420, datetime.now()))
        o1 = Option('call', security, 500, datetime(2020, 4, 20))
        o2 = Option('put', security, 300, datetime(2020, 4, 20))
        o3 = Option('call', security, 100, datetime(2020, 4, 20))  # ITM

        chain = OptionChain(security, datetime.now())
        chain.add_option(o1)
        chain.add_option(o2)
        chain.add_option(o3)

        calls, puts = chain.otm(datetime(2020, 4, 20)).values()
        self.assertEqual(1, len(calls))
        self.assertEqual(1, len(puts))

    def test_iv(self):
        security = Security('TSLA')
        security.add_quote(Quote(420, datetime.now()))
        o1 = Option('call', security, 700, datetime(2020, 4, 20))
        o3 = Option('call', security, 500, datetime(2020, 4, 20))
        o2 = Option('put', security, 400, datetime(2020, 4, 20))
        o1.iv = 5
        o1.price = 2
        o2.iv = 2
        o2.price = 4
        o3.iv = 0.5
        o3.price = 10

        chain = OptionChain(security, datetime.now())
        chain.add_option(o1)
        chain.add_option(o2)
        chain.add_option(o3)

        expected = (5 * 2 + 2 * 4 + 0.5 * 10) / (2 + 4 + 10)
        result = chain.iv(datetime(2020, 4, 20))
        self.assertEqual(expected, result)

    def test_option_expired(self):
        security = Security('TSLA')
        call = Option('call', security, 420, datetime(2020, 12, 4))
        self.assertTrue(call.expired(datetime(2020, 12, 4)))
        self.assertTrue(call.expired(datetime(2020, 12, 5)))

    def test_option_itm(self):
        security = Security('TSLA')
        call = Option('call', security, 420, datetime(2020, 12, 4))
        put = Option('put', security, 420, datetime(2020, 12, 4))
        self.assertTrue(call.itm(500))
        self.assertFalse(call.itm(400))
        self.assertTrue(put.itm(400))
        self.assertFalse(put.itm(500))

    def test_get_price(self):
        call = Option('call', TSLA, 420, datetime(2020, 12, 4))
        call.price = 420
        chain = OptionChain(TSLA, datetime.now())
        chain.add_option(call)

        self.assertEqual(420, chain.get_price(call))
