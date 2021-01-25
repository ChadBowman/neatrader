import unittest
from neatrader.math import min_max, un_min_max


class TestMath(unittest.TestCase):
    def test_min_max(self):
        a = [-5, 2, 1, 100, 48]
        mn = min(a)
        mx = max(a)
        for x in a:
            result = min_max(x, mn, mx)
            self.assertTrue(result <= 1 and result >= -1)

    def test_un_min_max(self):
        x = min_max(2, -5, 100)
        result = un_min_max(x, -5, 100)
        self.assertAlmostEqual(2, result, places=6)
