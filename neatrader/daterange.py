import random as rand
from datetime import timedelta
from neatrader.utils import days_between


class DateRangeFactory:
    def __init__(self, training):
        self.training = training
        self.training_duration = self._training_duration()

    def date_range_by_end_target(self, duration, end_target):
        """
        Returns a date range (start, end) that that ensures an end date
        that is a trading day with a closing price and includes duration
        amount of calendar days in the range. The start date is not guaranteed
        to be a trading day or have a closing price.
        """
        i = round(end_target / self.training_duration * len(self.training)-1)
        end = self.training.loc[i, 'date']
        start = end - timedelta(days=duration)
        return (start, end)

    def random_date_range(self, duration):
        end_date_target = rand.randint(duration, self.training_duration)
        return self.date_range_by_end_target(duration, end_date_target)

    def _training_duration(self):
        mn = min(self.training['date'])
        mx = max(self.training['date'])
        return days_between(mn, mx)
