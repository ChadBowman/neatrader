from heapq import heappush, heappop


class MaxHeapQuote:
    def __init__(self, quote):
        self.quote = quote

    def __lt__(self, other):
        return self.quote > other.quote


class QuoteService:
    def __init__(self):
        self.quotes = {}

    def add_quote(self, security, quote):
        quote = MaxHeapQuote(quote)
        quote_heap = self.quotes.get(security, [])
        if not quote_heap:
            self.quotes[security] = quote_heap
        heappush(quote_heap, quote)

    def quote(self, security):
        quotes = self.quotes.get(security)
        return quotes[0].quote if quotes else None

    def pop(self, security):
        return heappop(self.quotes.get(security)).quote
