import pandas as pd


class TradeReporter:
    def __init__(self):
        self.row_list = []
        self.fitness = 0.0

    def record(self, date, action, security, amt, price=None):
        record = {"date": date, "action": action, "security": security, "amt": amt, "price": price}
        self.row_list.append(record)

    def to_df(self):
        return pd.DataFrame(data=self.row_list)
