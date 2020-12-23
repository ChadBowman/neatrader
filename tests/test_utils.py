import unittest
from neatrader.utils import flatten_dict


class TestUtils(unittest.TestCase):
    def test_flatten_dict(self):
        a = {'a': 1, 'b': {'c': 2}}
        result = list(flatten_dict(a))
        assert 2 == len(result)
        assert 1 == result[0]
        assert 2 == result[1]
