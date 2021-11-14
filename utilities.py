import math
import time
import pandas as pd
import pdb
import calendar
import logging
logging.debug("This is a warning")


def update_df(df_to_update, df_updating, col_to_update, col_updating, join_on):
    ds_updating = df_updating[[join_on, col_updating]].set_index(join_on)
    ds_to_update = df_to_update[[join_on, col_to_update]].set_index(join_on)

    df_merged = ds_to_update.merge(
        ds_updating,
        left_on=ds_to_update.index,
        right_on=ds_updating.index,
        how="outer").fillna(0)

    df_to_update[col_to_update] = df_merged[col_updating]


def date_range(date_start, date_end):
    date_range = pd.date_range(
        start=date_start, end=date_end, freq='M')

    if date_start != end_of_month(date_start):
        date_range = date_range.insert(0, date_start)

    if date_end != end_of_month(date_end):
        date_range = date_range.append(pd.Index([date_end]))

    return date_range


def days_in_month(date_selected):
    return calendar.monthrange(date_selected.year, date_selected.month)[1]


def end_of_month(date_selected):
    last_day_in_month = days_in_month(date_selected)
    return date_selected.replace(day=last_day_in_month)


def payment_dates(date_start, date_end):
    if date_end == date_start:
        return pd.to_datetime(pd.Index([date_start]))

    else:
        date_range = pd.date_range(
            start=date_start, end=date_end, freq='M')
        #
        if date_end != end_of_month(date_end):
            date_range = date_range.append(pd.Index([date_end]))

        return pd.to_datetime(date_range)


def day_to_month_frac(date_start):
    remaining_days = (end_of_month(date_start) - date_start).days + 1
    return remaining_days / days_in_month(date_start)


def duration_months(date_start, date_end):
    if date_end is None:
        return 1
    else:
        whole_months = len(pd.date_range(
            start=end_of_month(date_start), end=end_of_month(date_end), freq='M')) - 2
        first_period = day_to_month_frac(date_start)
        last_period = date_end.day / days_in_month(date_end)

        return whole_months + first_period + last_period


def ds_days(df, date_column):
    return (df[date_column] - df[date_column].shift(1)).dt.days.fillna(0).astype(int)


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        print('%r (%r, %r) %2.2f sec' % (method.__name__, args, kw, te - ts))
        return result

    return timed
