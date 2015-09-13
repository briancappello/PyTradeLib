import os
import re
from pandas.io.common import urlencode as _encode_url
from pandas_datareader.data import _sanitize_dates

def _construct_url(symbol, start=None, end=None, interval=None):
    """
    Get historical data for the given name from quandl.
    Date format is datetime
    Returns a DataFrame.
    """
    start, end = _sanitize_dates(start, end)
    interval = interval or 'daily'

    # if no specific dataset was provided, default to free WIKI dataset
    if '/' not in symbol:
        symbol = 'WIKI/' + symbol

    url = 'https://www.quandl.com/api/v3/datasets/%s.csv?' % symbol

    query_params = {'start_date': start.strftime('%Y-%m-%d'),
                    'end_date': end.strftime('%Y-%m-%d'),
                    'collapse': interval}

    if 'QUANDL_API_KEY_' in os.environ:
        query_params['api_key'] = os.environ['QUANDL_API_KEY']

    return url + _encode_url(query_params)

def _deconstruct_url(url):
    def get_match(args):
        key, pattern = args
        regex = re.compile(pattern)
        return key, regex.search(url).groups()[0]

    return dict(map(get_match, {
            'dataset': r'datasets\/([A-Z_0-9]+)\/',
            'symbol': r'\/([A-Z_0-9]+)\.csv',
            'interval': r'collapse="?(\w+)"?',
        }.items()
    ))
