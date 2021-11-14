from utilities import payment_dates, duration_months, day_to_month_frac
import pandas as pd
import pdb
import logging
logging.debug("This is a warning")


class Cost:
    def __init__(self, type, amount, date_start, date_end=None):
        self.type = type
        self.amount = amount
        self.date_start = date_start
        self.date_end = date_end or date_start

    @property
    def schedule(self):
        # date range
        date_range = payment_dates(self.date_start, self.date_end)

        # cost schedule
        months_duration = duration_months(self.date_start, self.date_end)
        costs_per_whole_month = self.amount / months_duration
        schedule = [costs_per_whole_month for period in range(
            len(list(date_range)))]
        if self.date_end is not None:
            schedule[0] = costs_per_whole_month * \
                day_to_month_frac(self.date_start)
            schedule[-1] = self.amount - sum(schedule[: -1])

        return pd.Series(data=schedule, index=date_range)
