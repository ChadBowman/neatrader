import unittest
from datetime import datetime
from neatrader.model import Option, CallOption, PutOption, Security, OptionChain, Quote
from neatrader.preprocess import CsvImporter
from pathlib import Path
from utils import TSLA


class TestOptionChain(unittest.TestCase):
    def test_intrinsic(self):
        call = CallOption(TSLA, 420, datetime(2020, 9, 4))
        put = PutOption(TSLA, 420, datetime(2020, 9, 4))

        price_underlying = 500
        self.assertEqual(price_underlying - 420, call.intrinsic(price_underlying))
        self.assertEqual(0, put.intrinsic(price_underlying))

        price_underlying = 400
        self.assertEqual(0, call.intrinsic(price_underlying))
        self.assertEqual(420 - price_underlying, put.intrinsic(price_underlying))

    def test_extrinsic(self):
        call = CallOption(TSLA, 420, datetime(2020, 9, 4))
        put = PutOption(TSLA, 420, datetime(2020, 9, 4))

        price_underlying = 500
        self.assertEqual(100 - (price_underlying - 420), call.extrinsic(100, price_underlying))
        self.assertEqual(10, put.extrinsic(10, price_underlying))

        price_underlying = 400
        self.assertEqual(10, call.extrinsic(10, price_underlying))
        self.assertEqual(40 - (420 - price_underlying), put.extrinsic(40, price_underlying))

    def test__expirations_by_price_weighted_theta(self):
        importer = CsvImporter()
        chain = next(importer.chains(Path('tests/test_data/TSLA')))
        self.assertEqual('TSLA20200903', str(chain))

        expirations = chain._expirations_by_price_weighted_theta("call", 372.72)

        most_recent = sorted(expirations.items(), key=lambda item: item[1])[0]
        self.assertEqual(datetime(2020, 9, 4), most_recent[0])
        self.assertAlmostEqual(-5.38725256, most_recent[1], places=8)

    def test_search(self):
        importer = CsvImporter()
        chain = next(importer.chains(Path('tests/test_data/TSLA')))
        self.assertEqual('TSLA20200903', str(chain))

        result = chain.search(372.72, theta=-1.2863, delta=0.4955)
        # direction,expiration,strike,price,iv,delta,theta,vega
        # call,200918,420.0,32.45,1.155,0.4955,-1.2863,0.3296
        self.assertEqual(datetime(2020, 9, 18), result.expiration)
        self.assertEqual(420, result.strike)

    def test_search_using_zeros(self):
        importer = CsvImporter()
        chain = next(importer.chains(Path('tests/test_data/TSLA')))
        self.assertEqual('TSLA20200903', str(chain))

        result = chain.search(372.72, theta=0, delta=0)

        self.assertEqual(datetime(2022, 9, 16), result.expiration)
        self.assertEqual(1000, result.strike)

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
        call = CallOption(security, 420, datetime(2020, 12, 4))
        put = PutOption(security, 420, datetime(2020, 12, 4))
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
