import pandas as pd
import unittest
from datetime import datetime
from neatrader.daterange import DateRangeFactory
from neatrader.utils import days_between, from_small_date
from pathlib import Path


class TestDateRangeFactory(unittest.TestCase):
    def test_range_by_end_target(self):
        path = Path("tests/test_data/normalized/TSLA/training.csv")
        training = pd.read_csv(path, parse_dates=["date"], date_parser=from_small_date)
        dr = DateRangeFactory(training)

        duration = 40
        # test training.csv should have 61 records spanning 93 days
        # this should yield the latest possible range
        start, end = dr.date_range_by_end_target(duration, 93)
        self.assertEqual(datetime(2020, 9, 2), end)
        self.assertEqual(duration, days_between(start, end))

        # the earliest possible range
        start, end = dr.date_range_by_end_target(duration, duration)
        self.assertEqual(datetime(2020, 5, 30), start)
        self.assertEqual(duration, days_between(start, end))

    def test_random_date_range(self):
        path = Path("tests/test_data/normalized/TSLA/training.csv")
        training = pd.read_csv(path, parse_dates=["date"], date_parser=from_small_date)
        dr = DateRangeFactory(training)

        duration = 42
        start, end = dr.random_date_range(42)
        self.assertEqual(duration, days_between(start, end))
