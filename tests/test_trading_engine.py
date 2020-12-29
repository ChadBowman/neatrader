import unittest
from neatrader.trading import TradingEngine
from neatrader.model import Portfolio, Option, Security
from datetime import datetime
from utils import TSLA


class TestTradingEngine(unittest.TestCase):
    def test_assign_call(self):
        secs = {TSLA: 100}
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(420, secs, [call])
        te = TradingEngine()

        te.assign(port, call)

        self.assertEqual(420 + 50000, port.cash)
        self.assertEqual(0, port.securities[TSLA])

    def test_assign_put(self):
        put = Option('put', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(70000, {TSLA: 12}, [put])
        te = TradingEngine()

        te.assign(port, put)

        self.assertEqual(70000 - 50000, port.cash)
        self.assertEqual(112, port.securities[TSLA])

    def test_eval(self):
        call = Option('call', TSLA, 400, datetime(2020, 12, 28))
        put = Option('put', TSLA, 420, datetime(2020, 12, 28))
        port = Portfolio(50000, {TSLA: 100}, [call, put])
        te = TradingEngine([port])

        te.eval({TSLA: 410}, datetime(2020, 12, 28))

        self.assertEqual(50000 + 40000 - 42000, port.cash)
        self.assertEqual(100, port.securities[TSLA])

    def test_eval_no_security(self):
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        put = Option('put', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(50000, {TSLA: 100}, [call, put])
        te = TradingEngine([port])

        te.eval({Security('GOOG'): 650}, datetime(2020, 12, 28))

        self.assertEqual(50000, port.cash)
        self.assertEqual(100, port.securities[TSLA])

    def test_eval_not_expired(self):
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        put = Option('put', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(50000, {TSLA: 100}, [call, put])
        te = TradingEngine([port])

        te.eval({TSLA: 650}, datetime(2020, 12, 30))

        self.assertEqual(50000, port.cash)
        self.assertEqual(100, port.securities[TSLA])
