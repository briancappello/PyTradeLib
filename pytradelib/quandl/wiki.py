import os
import sys

from pandas.io.common import urlencode as _encode_url

from pytradelib.downloader import Downloader
from pytradelib.utils import _sanitize_dates, csv_to_df


class QuandlDailyWikiProvider(object):
    def __init__(self, api_key=None, batch_size=20, sleep=20):
        self._api_key = api_key
        self._downloader = Downloader(batch_size=batch_size, sleep=sleep)

    @property
    def api_key(self):
        return self._api_key

    @api_key.setter
    def api_key(self, api_key):
        self._api_key = api_key

    def download(self, symbols, start=None, end=None):
        if isinstance(symbols, str):
            url = self._construct_url(symbols, start, end)
            csv = self._downloader.download(url)
            return csv_to_df(csv)
        elif isinstance(symbols, (list, tuple)):
            urls = [self._construct_url(symbol, start, end)
                    for symbol in symbols]
        elif isinstance(symbols, dict):
            urls = [self._construct_url(symbol, d['start'], d['end'])
                    for symbol, d in symbols.items()]
        else:
            raise Exception('symbols must be a string, a list of strings, or a dict of string to start/end dates')

        results = {}
        for url, csv in self._downloader.download(urls):
            symbol, df = self._url_to_symbol(url), csv_to_df(csv)
            results[symbol] = df
            print('parsed results for ' + symbol)
        return results

    def _construct_url(self, symbol, start=None, end=None):
        """
        Get historical data for the given name from quandl.
        Date format is datetime
        Returns a DataFrame.
        """
        start, end = _sanitize_dates(start, end)

        # if no specific dataset was provided, default to free WIKI dataset
        if '/' not in symbol:
            symbol = 'WIKI/' + symbol

        url = 'https://www.quandl.com/api/v3/datasets/%s.csv?' % symbol

        query_params = {'start_date': start.strftime('%Y-%m-%d'),
                        'end_date': end.strftime('%Y-%m-%d'),
                        'collapse': 'daily'}

        if self._api_key or 'QUANDL_API_KEY' in os.environ:
            query_params['api_key'] = self._api_key or os.environ['QUANDL_API_KEY']
        else:
            print('Please provide your API key in the constructor, or set the QUANDL_API_KEY environment variable')
            sys.exit(1)

        return url + _encode_url(query_params)

    def _url_to_symbol(self, url):
        return url[url.rfind('/')+1:url.rfind('.csv')]
