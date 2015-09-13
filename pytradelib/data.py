
from pytradelib.utils import get_parse_symbols, csv_to_df
from pytradelib.quandl import _construct_url as construct_url_quandl
from pytradelib.quandl import _deconstruct_url as deconstruct_url_quandl


def get_symbols_quandl(symbols, start='2010-01-01', end='2010-08-31', interval=None):
    if not isinstance(symbols, list):
        symbols = [symbols]
    return get_parse_symbols(symbols, start, end, interval, construct_url_quandl, deconstruct_url_quandl, csv_to_df)
