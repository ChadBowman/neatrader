import unittest
from datetime import datetime
from neatrader.model import Security, Quote
from neatrader.quote_service import QuoteService

TSLA = Security("TSLA")


class TestQuoteService(unittest.TestCase):
    def test_latest_quote(self):
        service = QuoteService()
        first = Quote(100,  datetime(2020, 4, 1))
        second = Quote(200, datetime(2020, 4, 2))
        third = Quote(300,  datetime(2020, 4, 3))
        service.add_quote(TSLA, second)
        service.add_quote(TSLA, third)
        service.add_quote(TSLA, first)

        self.assertEqual(third, service.quote(TSLA))

    def test_pop_quote(self):
        service = QuoteService()
        first = Quote(100,  datetime(2020, 4, 1))
        second = Quote(200, datetime(2020, 4, 2))
        third = Quote(300,  datetime(2020, 4, 3))
        service.add_quote(TSLA, second)
        service.add_quote(TSLA, third)
        service.add_quote(TSLA, first)

        self.assertEqual(third, service.pop(TSLA))
        self.assertEqual(second, service.pop(TSLA))
        self.assertEqual(first, service.pop(TSLA))
