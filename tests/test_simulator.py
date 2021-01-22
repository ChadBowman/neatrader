import unittest
import pandas as pd
from utils import TSLA
from neatrader.model import Portfolio, Option
from neatrader.trading import Simulator
from neatrader.utils import days_between
from pathlib import Path
from datetime import datetime


class BuyAndHold:
    def activate(self, params):
        return (0, 0, 1, 0, 0)


class AlwaysSell:
    def activate(self, params):
        return (0, 1, 0, self.delta, self.theta)


class SellOnce:
    def __init__(self):
        self.sold = False

    def activate(self, params):
        if self.sold:
            return (0, 0, 1, 0, 0)  # hold
        else:
            self.sold = True
            return (0, 1, 0, self.delta, self.theta)


class TestSimulator(unittest.TestCase):
    def test_simulate_range(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})

        sim = Simulator(TSLA, portfolio, path)

        gen = sim._days_in_range('2020-6-1', '2020-7-31')
        self.assertEqual(pd.Timestamp('2020-6-8'), next(gen)['date'])
        self.assertEqual(32, len(list(gen)))

    def test_days_in_range(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})

        sim = Simulator(TSLA, portfolio, path)

        gen = sim._days_in_range(datetime(2020, 9, 7), datetime(2020, 9, 11))
        self.assertEqual(2, len(list(gen)))

    def test_close_no_op(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})

        sim = Simulator(TSLA, portfolio, path)

        # no contracts to close, no-op
        sim._buy(None)

        self.assertEqual(100, portfolio.securities[TSLA])

    def test_close_short_call(self):
        path = Path('tests/test_data/normalized/TSLA')
        call = Option('call', TSLA, 420, datetime(2020, 9, 11))
        portfolio = Portfolio(cash=144, securities={call: -1})

        sim = Simulator(TSLA, portfolio, path)
        sim._buy(datetime(2020, 9, 8))

        self.assertEqual(0, portfolio.securities[call])
        self.assertEqual(0, portfolio.cash)

    def test_open_short_call(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})

        sim = Simulator(TSLA, portfolio, path)
        sim._sell(
            datetime(2020, 9, 8),
            0.2734645354273816,  # normalized close for 9/8
            0.298,  # should target the 420 strike
            0.75  # should target 10/2 expiration
        )

        call = Option('call', TSLA, 420, datetime(2020, 10, 2))
        self.assertEqual(-1, portfolio.securities[call])
        self.assertEqual(100, portfolio.securities[TSLA])
        self.assertEqual(100, portfolio.collateral[TSLA])
        self.assertEqual(1777, portfolio.cash)

    def test_calculate_fitness(self):
        path = Path('tests/test_data/normalized/TSLA')
        call = Option('call', TSLA, 420, datetime(2020, 9, 11))
        portfolio = Portfolio(cash=10, securities={TSLA: 100, call: -1})

        sim = Simulator(TSLA, portfolio, path)
        actual = sim._calculate_fitness(0.2990607757568724, datetime(2020, 9, 8))  # 420.28
        # starting cash + value of shares - call obligation - buy-and-hold value
        expected = 10 + (420.28 * 100) - (1.44 * 100) - (420.28 * 100)
        self.assertAlmostEqual(expected, actual, places=2)

    def test_hold_only(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        sim = Simulator(TSLA, portfolio, path)
        net = BuyAndHold()

        fitness = sim.simulate(net, datetime(2020, 9, 8), datetime(2020, 9, 11))

        # TSLA closed at 372.72 on 9/11
        # buy-and-hold is the fitness base-line
        self.assertAlmostEqual(0, fitness, places=3)

    def test_sell_and_get_assigned(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        sim = Simulator(TSLA, portfolio, path)
        net = AlwaysSell()
        net.theta = 0.637095  # target 9/18 expiration
        net.delta = 0.1328  # target 440 strike since close on 9/18 was 442.15

        fitness = sim.simulate(net, datetime(2020, 9, 10), datetime(2020, 9, 18))

        # premium + assigned cash - buy-and-hold value
        expected = (3.25 * 100) + (440 * 100) - (442.15 * 100)
        self.assertAlmostEqual(expected, fitness, places=2)
        self.assertEqual(0, portfolio.securities[TSLA])
        self.assertEqual(0, portfolio.collateral[TSLA])
        self.assertEqual(44325, portfolio.cash)

    def test_sell_and_expire(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        sim = Simulator(TSLA, portfolio, path)
        net = SellOnce()
        net.theta = 0.637095  # target 9/18 expiration
        net.delta = 0.1249  # target 445 strike since close on 9/18 was 442.15

        fitness = sim.simulate(net, datetime(2020, 9, 8), datetime(2020, 9, 18))

        # premium + held shares value - buy-and-hold value
        expected = (2.9 * 100) + (442.15 * 100) - (442.15 * 100)
        self.assertAlmostEqual(expected, fitness, places=2)
        self.assertEqual(100, portfolio.securities[TSLA])
        self.assertEqual(0, portfolio.collateral[TSLA])
        self.assertEqual(290, portfolio.cash)

    def test_expire_without_close_on_expiration(self):
        path = Path('tests/test_data/normalized/TSLA')
        call = Option('call', TSLA, 2800, datetime(2020, 7, 24))
        portfolio = Portfolio(cash=0, securities={TSLA: 100, call: -1})
        portfolio.collateral = {TSLA: 100}
        sim = Simulator(TSLA, portfolio, path)
        net = BuyAndHold()

        sim.simulate(net, datetime(2020, 7, 23), datetime(2020, 8, 3))

        self.assertEqual(0, portfolio.securities.get(call, 0))

    def test_range_by_end_target(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio()
        sim = Simulator(TSLA, portfolio, path)

        duration = 90
        # test ta.csv should have 184 records spanning 275 days
        # this should yield the latest possible range
        start, end = sim._date_range_by_end_target(duration, 275)
        self.assertEqual(datetime(2020, 10, 2), end)
        self.assertEqual(duration, days_between(start, end))

        # the earliest possble range
        start, end = sim._date_range_by_end_target(duration, duration)
        self.assertEqual(datetime(2019, 12, 31), start)
        self.assertEqual(duration, days_between(start, end))

    def test_random_date_range(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio()
        sim = Simulator(TSLA, portfolio, path)

        duration = 42
        start, end = sim._random_date_range(42)
        self.assertEqual(duration, days_between(start, end))
