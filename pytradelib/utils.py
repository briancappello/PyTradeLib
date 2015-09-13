import os
import pandas as pd

pd.set_option('io.hdf.default_format', 'table')

from pandas import HDFStore
from pandas.compat import StringIO, bytes_to_str

import grequests
from gevent import monkey
monkey.patch_all()

DATA_DIR = os.environ['HOME'] + '/.pytradelib'
__STORE = None


def _bulk_download(urls):
    return grequests.imap((grequests.get(url) for url in urls))

def get_parse_symbols(symbols, start, end, interval, symbol_to_url, url_to_symbol, data_to_df):
    urls = (symbol_to_url(symbol.upper(), start, end, interval) for symbol in symbols)
    def parse_response_to_symbol_and_df(r):
        return url_to_symbol(r.url), data_to_df(r.text)
    data = map(parse_response_to_symbol_and_df, _bulk_download(urls))
    bulk_persist(data)
    return data

def csv_to_df(text):
    rs = pd.read_csv(StringIO(bytes_to_str(text)), index_col=0,
                     parse_dates=True, na_values='-')[::-1]

    # Yahoo! Finance sometimes does this awesome thing where they
    # return 2 rows for the most recent business day
    if len(rs) > 2 and rs.index[-1] == rs.index[-2]: # pragma: no cover
        rs = rs[:-1]

    # Get rid of unicode characters in index name.
    try:
        rs.index.name = rs.index.name.decode('unicode_escape').encode('ascii', 'ignore')
    except AttributeError:
        # Python 3 string has no decode method.
        rs.index.name = rs.index.name.encode('ascii', 'ignore').decode()
    return rs

def get_store():
    global __STORE
    if not __STORE:
        if not os.path.exists(DATA_DIR):
            os.mkdir(DATA_DIR)
        __STORE = HDFStore(DATA_DIR + '/store.hdf5')
    return __STORE

def store_path(symbol, interval):
    return '/symbols/%s/%s' % (symbol.upper(), interval.lower())

def exists(symbol, interval):
    store = get_store()
    return store_path(symbol, interval) in store.keys()

def persist(symbol, interval, df):
    store = get_store()
    if exists(symbol, interval):
        store.append(store_path(symbol, interval), df)
    else:
        store.put(store_path(symbol, interval), df)

def bulk_persist(data):
    for symbol_data, df in data:
        persist(symbol_data['symbol'], symbol_data['interval'], df)

def most_recent_datetime(symbol, interval):
    store = get_store()
    return store.get(store_path(symbol, interval)).tail(1).index[0].to_datetime()
