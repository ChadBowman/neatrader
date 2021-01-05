import unittest
from neatrader.trading import TradingEngine
from neatrader.model import Portfolio, Option, Security
from datetime import datetime
from utils import TSLA


class TestTradingEngine(unittest.TestCase):
    def test_assign_call(self):
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        secs = {TSLA: 100, call: 1}
        port = Portfolio(420, secs)
        te = TradingEngine()

        te.assign(port, call)

        self.assertEqual(420 + 50000, port.cash)
        self.assertEqual(0, port.securities[TSLA])

    def test_assign_put(self):
        put = Option('put', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(70000, {TSLA: 12, put: 1})
        te = TradingEngine()

        te.assign(port, put)

        self.assertEqual(70000 - 50000, port.cash)
        self.assertEqual(112, port.securities[TSLA])

    def test_eval(self):
        call = Option('call', TSLA, 400, datetime(2020, 12, 28))
        put = Option('put', TSLA, 420, datetime(2020, 12, 28))
        port = Portfolio(50000, {TSLA: 200, call: 2, put: 2})
        te = TradingEngine([port])

        te.eval({TSLA: 410}, datetime(2020, 12, 28))

        self.assertEqual(50000 + (40000 * 2) - (42000 * 2), port.cash)
        self.assertEqual(200, port.securities[TSLA])

    def test_eval_no_security(self):
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        put = Option('put', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(50000, {TSLA: 100, call: 1, put: 1})
        te = TradingEngine([port])

        te.eval({Security('GOOG'): 650}, datetime(2020, 12, 28))

        self.assertEqual(50000, port.cash)
        self.assertEqual(100, port.securities[TSLA])

    def test_eval_not_expired(self):
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        put = Option('put', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(50000, {TSLA: 100, call: 1, put: 1})
        te = TradingEngine([port])

        te.eval({TSLA: 650}, datetime(2020, 12, 30))

        self.assertEqual(50000, port.cash)
        self.assertEqual(100, port.securities[TSLA])

    def test_buy_contract(self):
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(1000, {})
        te = TradingEngine([port])

        te.buy_contract(port, call, 10)

        self.assertEqual(0, port.cash)
        self.assertEqual(1, port.securities[call])

    def test_sell_contract(self):
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(0, {TSLA: 100})
        te = TradingEngine([port])

        te.sell_contract(port, call, 10)

        self.assertEqual(1000, port.cash)
        self.assertEqual(-1, port.securities[call])

    def test_sell_too_many_contracts(self):
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(0, {TSLA: 100})
        te = TradingEngine([port])

        te.sell_contract(port, call, 10)
        self.assertRaises(Exception, te.sell_contract, port, call, 10)

    def test_release_collateral(self):
        call = Option('call', TSLA, 500, datetime(2020, 12, 28))
        port = Portfolio(50000, {TSLA: 100})
        te = TradingEngine([port])

        # sell a contract to start, putting up 100 shares as collateral
        te.sell_contract(port, call, 10)
        self.assertEqual(-1, port.securities[call])
        self.assertEqual(100, port.collateral[TSLA])

        # buy back the contract, eliminating the obligation
        te.buy_contract(port, call, 10)
        self.assertEqual(0, port.securities[call])
        self.assertEqual(0, port.collateral[TSLA])

        # go long instead, purchasing a call
        te.buy_contract(port, call, 10)
        self.assertEqual(1, port.securities[call])
        self.assertEqual(0, port.collateral[TSLA])

        # close that long call
        te.sell_contract(port, call, 10)
        self.assertEqual(0, port.securities[call])
        self.assertEqual(0, port.collateral[TSLA])

        # sell an option to go short again
        te.sell_contract(port, call, 10)
        self.assertEqual(-1, port.securities[call])
        self.assertEqual(100, port.collateral[TSLA])
