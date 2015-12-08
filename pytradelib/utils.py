from __future__ import print_function

import time
import pytz
import pandas as pd

from pandas.compat import StringIO, bytes_to_str
from pandas.core.datetools import to_datetime

from datetime import datetime


def batch(list_, size, sleep=None):
    list_ = list(list_)
    len_ = len(list_)
    for i in xrange((len_ / size) + 1):
        start_idx = i * size
        end_idx = (i + 1) * size
        if end_idx > len_:
            end_idx = len_
        result = list_[start_idx:end_idx]
        if result:
            yield result
        if sleep:
            print('Sleeping for %d seconds' % sleep)
            time.sleep(sleep)


def _sanitize_dates(start, end):
    start = to_datetime(start)
    end = to_datetime(end)
    if start is None:
        start = datetime(1900, 1, 1)
    if end is None:
        end = datetime.today()
    return start, end


def csv_to_df(text):
    df = pd.read_csv(StringIO(bytes_to_str(text)), index_col=0,
                     parse_dates=True, infer_datetime_format=True,
                     na_values='-')[::-1]

    # Yahoo! Finance sometimes does this awesome thing where they
    # return 2 rows for the most recent business day
    if len(df) > 2 and df.index[-1] == df.index[-2]:  # pragma: no cover
        df = df[:-1]

    # Get rid of unicode characters in index name.
    try:
        df.index.name = df.index.name.decode('unicode_escape').encode('ascii', 'ignore')
    except AttributeError:
        # Python 3 string has no decode method.
        df.index.name = df.index.name.encode('ascii', 'ignore').decode()

    column_renames = {'Adj. Open': 'Adj Open', 'Adj. High': 'Adj High',
                      'Adj. Low': 'Adj Low', 'Adj. Close': 'Adj Close',
                      'Adj. Volume': 'Adj Volume'}
    df.rename(columns=column_renames, inplace=True)
    return df.tz_localize(pytz.UTC)


def percent_change(from_val, to_val):
    # coerce to float for decimal division
    diff = float(to_val) - from_val
    return (diff / from_val) * 100


def crossed(value, yesterday, today, use_adjusted=True):
    def key(price_key):
        return 'Adj ' + price_key if use_adjusted else price_key
    crossed_over = yesterday[key('Close')] < value < today[key('Close')]
    crossed_under = yesterday[key('Close')] > value > today[key('Close')]
    return crossed_over or crossed_under


def within_percent_of_value(price, value, percent=1):
    diff = percent * 0.01 * 0.5 * value
    return (value - diff) < price < (value + diff)
