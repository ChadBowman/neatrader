import unittest
import pandas as pd
from utils import TSLA
from neatrader.model import Portfolio, Option
from neatrader.trading import Simulator
from neatrader.preprocess import CsvImporter
from pathlib import Path
from datetime import datetime


class BuyAndHold:
    def activate(self, params):
        return (0, 0, 1, 0, 0)


class AlwaysSell:
    def activate(self, params):
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
        importer = CsvImporter()

        sim = Simulator(TSLA, portfolio, path)
        chain = importer.parse_chain(datetime(2020, 9, 8), TSLA, path / 'chains' / '200908.csv')
        sim._buy(chain)

        self.assertEqual(0, portfolio.securities[call])
        self.assertEqual(0, portfolio.cash)

    def test_open_short_call(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        importer = CsvImporter()

        sim = Simulator(TSLA, portfolio, path)
        chain = importer.parse_chain(datetime(2020, 9, 8), TSLA, path / 'chains' / '200908.csv')
        sim._sell(
            chain,
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
        importer = CsvImporter()
        chain = importer.parse_chain(datetime(2020, 9, 8), TSLA, path / 'chains' / '200908.csv')

        sim = Simulator(TSLA, portfolio, path)
        actual = sim._calculate_fitness(0.2990607757568724, chain)  # 420.28
        expected = 10 + (420 * 100) - (1.44 * 100)
        self.assertAlmostEqual(expected, actual, places=-2)

    def test_hold_only(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        sim = Simulator(TSLA, portfolio, path)
        net = BuyAndHold()

        fitness = sim.simulate(net, datetime(2020, 9, 8), datetime(2020, 9, 11))

        # TSLA closed at 372.72 on 9/11
        self.assertAlmostEqual(100 * 372.72, fitness, places=3)

    def test_sell_and_get_assigned(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        sim = Simulator(TSLA, portfolio, path)
        net = AlwaysSell()
        net.theta = 0.637095  # target 9/18 expiration
        net.delta = 0.1328  # target 440 strike since close on 9/18 was 442.15

        fitness = sim.simulate(net, datetime(2020, 9, 10), datetime(2020, 9, 18))

        expected = (3.25 * 100) + (440 * 100)
        self.assertAlmostEqual(expected, fitness, places=2)
        self.assertEqual(0, portfolio.securities[TSLA])
        self.assertEqual(0, portfolio.collateral[TSLA])
        self.assertEqual(expected, portfolio.cash)

    def test_sell_and_expire(self):
        path = Path('tests/test_data/normalized/TSLA')
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        sim = Simulator(TSLA, portfolio, path)
        net = AlwaysSell()
        net.theta = 0.637095  # target 9/18 expiration
        net.delta = 0.1249  # target 445 strike since close on 9/18 was 442.15

        fitness = sim.simulate(net, datetime(2020, 9, 10), datetime(2020, 9, 18))

        expected = (2.9 * 100) + (442.15 * 100)
        self.assertAlmostEqual(expected, fitness, places=2)
        self.assertEqual(100, portfolio.securities[TSLA])
        self.assertEqual(0, portfolio.collateral[TSLA])
        self.assertEqual(290, portfolio.cash)
