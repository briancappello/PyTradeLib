

from pytradelib.utils import batch
from pytradelib.downloader import Downloader

from urllib import urlencode
try:
    import simplejson as json
except ImportError:
    import json


def get_yql_url(yql):
    base_url = 'http://query.yahooapis.com/v1/public/yql?'
    url = base_url + urlencode({'q': yql,
                                 'env': 'store://datatables.org/alltableswithkeys',
                                 'format': 'json'})
    if len(url) > (2 * 1024):
        raise Exception('URL must be shorter than 2048 characters')
    return url


_EXCHANGES = {
    'ASE': 'AMEX',
    'NYQ': 'NYSE',
    'NMS': 'NASDAQ',  # 'NasdaqGS',
    'NGM': 'NASDAQ',  # 'NasdaqGM',
    'NCM': 'NASDAQ',  # 'NasdaqCM',
}


def _convert_result(result):
    """
    Converts a YQL result dictionary into PyTradeLib format
    :param result: dict
    :return: dict with keys lowercased
    """
    r = {}
    for k, v in result.items():
        if k == 'StockExchange':
            k = 'exchange'
            v = _EXCHANGES.get(v, None)
        if k == 'ErrorIndicationreturnedforsymbolchangedinvalid':
            k = 'error'
        if k == 'LastTradeDate':
            k = 'last_trade_date'
        r[k.lower()] = v
    return r


def get_symbols_info(symbols, keys=None):
    if not isinstance(symbols, (list, tuple)):
        symbols = list(symbols)
    keys = keys or ['Symbol', 'Name', 'StockExchange', 'LastTradeDate']
    yql = 'select %(keys)s from yahoo.finance.quotes where symbol in (%(symbols)s)'

    urls = []
    for batched_symbols in batch(symbols, 100):
        csv_symbols = ','.join(['"%s"' % s.upper() for s in batched_symbols])
        urls.append(get_yql_url(yql % {'keys': ','.join(keys),
                                       'symbols': csv_symbols}))
    downloader = Downloader()

    results = []
    for url, text in downloader.download(urls):
        json_ = json.loads(text)
        for result in json_['query']['results']['quote']:
            results.append(_convert_result(result))
    return results
