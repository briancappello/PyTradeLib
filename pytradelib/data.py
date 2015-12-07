import os
from datetime import datetime
from pytradelib.store import CSVStore
from pytradelib.quandl.wiki import QuandlDailyWikiProvider
from pytradelib.settings import DATA_DIR

class DataManager(object):
    def __init__(self, store=None, data_provider=None):
        self._store = store or CSVStore()
        self._provider = data_provider or QuandlDailyWikiProvider()

    def initialize_store(self):
        raise NotImplementedError

    def update_store(self):
        symbols = dict([ (symbol, {'start': self._store.get_end_date(symbol),
                                   'end': datetime.now()} )\
                         for symbol in self._store.symbols ])
        self._store.set_dfs(self._provider.download(symbols))

    def analyze(self):
        results = self._store.analyze()
        filename = '%s-analysis.csv' % datetime.now().strftime('%Y-%m-%d')
        results.to_csv(os.path.join(DATA_DIR, filename))
        return results

if __name__ == '__main__':
    data_manager = DataManager(CSVStore(), QuandlDailyWikiProvider())
    data_manager.update_store()
