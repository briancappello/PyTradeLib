import os
import sys
import pytz
import pandas as pd
from pandas.tseries.offsets import DateOffset
from datetime import date, datetime
from collections import defaultdict

from pytradelib.store import CSVStore
from pytradelib.quandl.wiki import QuandlDailyWikiProvider
from pytradelib.quandl.metadata import get_symbols_list
from pytradelib.yahoo.yql import get_symbols_info
from pytradelib.settings import DATA_DIR
from pytradelib.logger import logger


class DataManager(object):
    def __init__(self, store=None, data_provider=None):
        self._store = store or CSVStore()
        self._provider = data_provider or QuandlDailyWikiProvider(batch_size=30)

    def initialize_store(self):
        symbols = get_symbols_list('WIKI')
        info = get_symbols_info(symbols)

        # HACK: find the most recent valid trade date by searching through
        # all of the last_trade_dates for the most frequent date
        dates = defaultdict(lambda: 0)
        for d in info:
            dates[d['last_trade_date']] += 1
        items = dates.items()
        items.sort(key=lambda x: x[1])
        last_valid_trade_date = items[-1][0]
        logger.debug('last_valid_trade_date: %s' % last_valid_trade_date)

        # filter out all symbols which are no longer active
        symbols = [d['symbol'] for d in info
                   if d['last_trade_date'] == last_valid_trade_date]
        logger.debug('expecting %d symbols' % len(symbols))

        # download daily data
        self._store.set_dfs(self._provider.download(symbols))

    def update_store(self):
        last_trading_day = pd.Timestamp(date.today(), tz=pytz.UTC)
        while last_trading_day.weekday() > 4:
            last_trading_day = last_trading_day - DateOffset(days=1)

        symbols = {}
        for symbol in self._store.symbols:
            latest_dt = self._store.get_end_date(symbol)
            if latest_dt != last_trading_day:
                symbols[symbol] = {'start': latest_dt, 'end': last_trading_day}

        if not symbols:
            return []

        self._store.set_dfs(self._provider.download(symbols))
        return symbols.keys()

    def analyze(self):
        results = self._store.analyze()
        filename = '%s-analysis.csv' % datetime.now().strftime('%Y-%m-%d')
        filepath = os.path.join(DATA_DIR, filename)
        results.to_csv(filepath)
        return results


if __name__ == '__main__':
    data_manager = DataManager(CSVStore(), QuandlDailyWikiProvider())
    # data_manager.update_store()
    data_manager.analyze()
