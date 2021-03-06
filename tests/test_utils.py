import unittest
from neatrader.utils import flatten_dict, days_between
from datetime import datetime


class TestUtils(unittest.TestCase):
    def test_flatten_dict(self):
        a = {'a': 1, 'b': {'c': 2}}
        result = list(flatten_dict(a))
        assert 2 == len(result)
        assert 1 == result[0]
        assert 2 == result[1]

    def test_days_between(self):
        result = days_between(datetime(2021, 1, 1), datetime(2021, 2, 1))
        self.assertEqual(31, result)
