import unittest
from neatrader.model import Security, Quote
from datetime import datetime


class TestSecurity(unittest.TestCase):
    def test_last_quote(self):
        security = Security('TSLA')
        security.add_quote(Quote(100, datetime(2021, 1, 1)))
        security.add_quote(Quote(99, datetime(2021, 1, 2)))

        self.assertEqual(datetime(2021, 1, 2), security.last_quote().date)
