import unittest
import pandas as pd
from utils import TSLA
from neatrader.model import Portfolio, Option
from neatrader.trading import Simulator
from neatrader.utils import from_small_date
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


class Log:
    def activate(self, params):
        print(params)
        return (0, 1, 0, self.delta, self.theta)


class TestSimulator(unittest.TestCase):
    def test_simulate_range(self):
        path = Path('tests/test_data/normalized/TSLA')
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        portfolio = Portfolio(cash=0, securities={TSLA: 100})

        sim = Simulator(TSLA, portfolio, path, training)

        gen = sim._days_in_range('2020-6-1', '2020-7-31')
        self.assertEqual(pd.Timestamp('2020-6-2'), next(gen)['date'])
        self.assertEqual(36, len(list(gen)))

    def test_days_in_range(self):
        path = Path('tests/test_data/normalized/TSLA')
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        portfolio = Portfolio(cash=0, securities={TSLA: 100})

        sim = Simulator(TSLA, portfolio, path, training)

        # span a weekend
        gen = sim._days_in_range(datetime(2020, 7, 10), datetime(2020, 7, 14))
        self.assertEqual(2, len(list(gen)))

    def test_close_no_op(self):
        path = Path('tests/test_data/normalized/TSLA')
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        portfolio = Portfolio(cash=0, securities={TSLA: 100})

        sim = Simulator(TSLA, portfolio, path, training)

        # no contracts to close, no-op
        sim._buy(None)

        self.assertEqual(100, portfolio.securities[TSLA])

    def test_close_short_call(self):
        path = Path('tests/test_data/normalized/TSLA')
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        call = Option('call', TSLA, 420, datetime(2020, 7, 17))
        portfolio = Portfolio(cash=133535, securities={call: -1})

        sim = Simulator(TSLA, portfolio, path, training)
        sim._buy(datetime(2020, 7, 14))

        self.assertEqual(0, portfolio.securities[call])
        self.assertEqual(0, portfolio.cash)

    def test_open_short_call(self):
        path = Path('tests/test_data/normalized/TSLA')
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        portfolio = Portfolio(cash=0, securities={TSLA: 100})

        sim = Simulator(TSLA, portfolio, path, training)
        sim._sell(
            datetime(2020, 7, 20),
            0.293070701634208,   # normalized close for 7/20
            0.4617712204180135,  # should target the 2000 strike
            0.3087888191319731   # should target 8/21 expiration
        )

        call = Option('call', TSLA, 2000, datetime(2020, 8, 21))
        self.assertEqual(-1, portfolio.securities[call])
        self.assertEqual(100, portfolio.securities[TSLA])
        self.assertEqual(100, portfolio.collateral[TSLA])
        self.assertEqual(10875, portfolio.cash)

    def test_calculate_fitness(self):
        path = Path('tests/test_data/normalized/TSLA')
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        call = Option('call', TSLA, 420, datetime(2020, 9, 11))
        portfolio = Portfolio(cash=10, securities={TSLA: 100, call: -1})

        sim = Simulator(TSLA, portfolio, path, training)
        actual = sim._calculate_fitness(0.2990607757568724, datetime(2020, 9, 8))  # 420.28
        # starting cash + value of shares - call obligation - buy-and-hold value
        expected = 10 + (420.28 * 100) - (1.44 * 100) - (420.28 * 100)
        self.assertAlmostEqual(expected, actual, places=2)

    def test_hold_only(self):
        path = Path('tests/test_data/normalized/TSLA')
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        sim = Simulator(TSLA, portfolio, path, training)
        net = BuyAndHold()

        fitness = sim.simulate(net, datetime(2020, 7, 20), datetime(2020, 8, 22))

        # close on 8/21 was 2049.98
        # buy-and-hold is the fitness base-line
        self.assertAlmostEqual(0, fitness, places=3)

    def test_sell_and_get_assigned(self):
        path = Path('tests/test_data/normalized/TSLA')
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        sim = Simulator(TSLA, portfolio, path, training)
        net = SellOnce()

        # close on 8/21 was 2049.98
        # direction,expiration,strike,price,iv,delta,theta,vega
        # call,200821,2000.0,108.75,0.4965503408681624,0.46177122041801355,0.30752325473559794,0.5241433005010039
        net.theta = 0.3087888191319731  # target 8/21 expiration
        net.delta = 0.4617712204180135  # target 2000 strike

        fitness = sim.simulate(net, datetime(2020, 7, 19), datetime(2020, 8, 22))

        # premium + assigned cash - buy-and-hold value
        expected = (108.75 * 100) + (2000 * 100) - (2049.98 * 100)
        self.assertAlmostEqual(expected, fitness, places=2)
        self.assertEqual(0, portfolio.securities[TSLA])
        self.assertEqual(0, portfolio.collateral[TSLA])
        self.assertEqual(10875 + 200000, portfolio.cash)

    def test_sell_and_expire(self):
        path = Path('tests/test_data/normalized/TSLA')
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        portfolio = Portfolio(cash=0, securities={TSLA: 100})
        sim = Simulator(TSLA, portfolio, path, training)
        net = SellOnce()

        # close on 8/21 was 2049.98
        # direction,expiration,strike,price,iv,delta,theta,vega
        # call,200821,2050.0,100.0,0.49691698172618826,0.4607403125936822,0.3105944110992971,0.5219995298370175
        net.theta = 0.3087888191319731  # target 8/21 expiration
        net.delta = 0.4607403125936822  # target 2050 strike

        fitness = sim.simulate(net, datetime(2020, 7, 19), datetime(2020, 8, 22))

        # premium + held shares value - buy-and-hold value
        expected = (100 * 100) + (2049.98 * 100) - (2049.98 * 100)
        self.assertAlmostEqual(expected, fitness, places=2)
        self.assertEqual(100, portfolio.securities[TSLA])
        self.assertEqual(0, portfolio.collateral[TSLA])
        self.assertEqual(10000, portfolio.cash)

    def test_expire_without_close_on_expiration(self):
        path = Path('tests/test_data/normalized/TSLA')
        training = pd.read_csv(path / 'training.csv', parse_dates=['date'], date_parser=from_small_date)
        call = Option('call', TSLA, 2800, datetime(2020, 7, 24))
        portfolio = Portfolio(cash=0, securities={TSLA: 100, call: -1})
        portfolio.collateral = {TSLA: 100}
        sim = Simulator(TSLA, portfolio, path, training)
        net = BuyAndHold()

        sim.simulate(net, datetime(2020, 7, 23), datetime(2020, 8, 3))

        self.assertEqual(0, portfolio.securities.get(call, 0))
