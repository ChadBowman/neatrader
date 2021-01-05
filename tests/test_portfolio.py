import unittest
from neatrader.model import Portfolio, Option
from utils import TSLA
from datetime import datetime


class TestPortfolio(unittest.TestCase):
    def test_contracts(self):
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        p = Portfolio(0, {call: 1})

        self.assertEqual(1, p.contracts()[call])

    def test_stocks(self):
        p = Portfolio(0, {TSLA: 1})
        self.assertEqual(1, p.stocks()[TSLA])
