import unittest
from neatrader.trading import StockSplitHandler
from neatrader.model import Portfolio, Option
from utils import TSLA
from pathlib import Path
from datetime import datetime


class TestStockSplitHandler(unittest.TestCase):
    def test_check_and_invoke_stocks(self):
        ss = StockSplitHandler(Path('tests/test_data/TSLA/splits.csv'), TSLA)
        p = Portfolio(securities={TSLA: 3})

        ss.check_and_invoke(p, datetime(2020, 8, 31))

        self.assertEqual(1, len(p.securities))
        self.assertEqual(3 * 5, p.securities[TSLA])

    def test_check_and_invoke_contracts(self):
        call = Option('call', TSLA, 420, datetime(2021, 4, 20))
        call.price = 35
        p = Portfolio(securities={call: -1})
        ss = StockSplitHandler(Path('tests/test_data/TSLA/splits.csv'), TSLA)

        ss.check_and_invoke(p, datetime(2020, 8, 31))
        new_call = Option('call', TSLA, 420 / 5, datetime(2021, 4, 20))

        contract = next(iter(p.securities.keys()))
        self.assertEqual(1, len(p.securities))
        self.assertEqual(-1 * 5, p.securities[new_call])
        self.assertEqual(7, contract.price)
        self.assertEqual(420 / 5, contract.strike)
