import os
import pytz
import talib as ta
import pandas as pd
from pandas.tseries.offsets import DateOffset

from pytradelib.settings import DATA_DIR, ZIPLINE_CACHE_DIR
from pytradelib.utils import (
    percent_change,
    within_percent_of_value,
    crossed,
)


class CSVStore(object):
    _symbols = []
    _csv_files = {}
    _start_dates = {}
    _end_dates = {}
    _df_cache = {}

    def __init__(self):
        self._store_contents = self._get_store_contents()
        for d in self._store_contents:
            symbol = d['symbol']
            self._symbols.append(symbol)
            self._csv_files[symbol] = d['csv_path']
            self._start_dates[symbol] = d['start']
            self._end_dates[symbol] = d['end']

    @property
    def symbols(self):
        return self._symbols

    def get_df(self, symbol, start=None, end=None):
        symbol = symbol.upper()
        def to_timestamp(dt, default):
            if dt:
                return pd.Timestamp(dt, tz=pytz.UTC)
            return default
        start = to_timestamp(start, 0)
        end = to_timestamp(end, None)

        df = self._df_cache.get(symbol, None)
        if df is None:
            csv_path = self._csv_files[symbol]
            df = pd.DataFrame.from_csv(csv_path).tz_localize(pytz.UTC)
            self._df_cache[symbol] = df
        return df[start:end]

    def set_df(self, symbol, df):
        self._update_df(symbol, df)

    def _update_df(self, symbol, df):
        symbol = symbol.upper()
        if symbol in self.symbols:
            existing_df = self.get_df(symbol)
            df = existing_df.append(df[existing_df.index[-1] + DateOffset(days=1):])
            os.remove(self.get_csv_path(symbol))
        df = self._add_ta(df)
        csv_path = self._get_store_path(symbol, df.index[0], df.index[-1])
        df.to_csv(csv_path)
        self._set_csv_path(symbol, csv_path)
        self._set_end_date(symbol, df.index[-1])
        self._df_cache[symbol] = df

    def get_dfs(self, symbols=None, start=None, end=None):
        symbols = symbols or self.symbols
        if not isinstance(symbols, list):
            symbols = [symbols]
        return dict(zip(
            [symbol.upper() for symbol in symbols],
            [self.get_df(symbol, start, end) for symbol in symbols]
        ))

    def set_dfs(self, symbol_df_dict):
        for symbol, df in symbol_df_dict.items():
            self.set_df(symbol, df)

    def analyze(self, symbols=None, use_adjusted=True):
        '''
        :param symbols: list of symbols (defaults to all in the store)
        :param use_adjusted: whether or not to use adjusted prices
        :return: DataFrame
        '''
        def key(price_key):
            return 'Adj ' + price_key if use_adjusted else price_key

        results = {}
        for symbol, df in self.get_dfs(symbols).items():
            today = df.iloc[-1]
            yesterday = df.iloc[-2]
            most_recent_year = df[df.index[-1] - DateOffset(years=1):]
            year_low = most_recent_year[key('Low')][:-1].min()
            year_high = most_recent_year[key('High')][:-1].max()
            dollar_volume_desc = most_recent_year.dollar_volume.describe()

            results[symbol] = {
                # last-bar metrics
                'previous_close': yesterday[key('Close')],
                'close': today[key('Close')],
                'percent_change': percent_change(yesterday[key('Close')], today[key('Close')]),
                'dollar_volume': today.dollar_volume,
                'percent_of_median_volume': (today.Volume * today[key('Close')]) / dollar_volume_desc['50%'],
                'advancing': today[key('Close')] > yesterday[key('Close')],
                'declining': today[key('Close')] < yesterday[key('Close')],
                'new_low': today[key('Close')] < year_low,
                'new_high': today[key('Close')] > year_high,
                'percent_of_high': today[key('Close')] / year_high,
                'near_sma100': within_percent_of_value(today[key('Close')], today['sma100'], 2),
                'near_sma200': within_percent_of_value(today[key('Close')], today['sma200'], 2),
                'crossed_sma100': crossed(today['sma100'], yesterday, today),
                'crossed_sma200': crossed(today['sma200'], yesterday, today),

                # stock "health" metrics
                'year_high': year_high,
                'year_low': year_low,
                'min_volume': int(dollar_volume_desc['min']),
                'dollar_volume_25th_percentile': int(dollar_volume_desc['25%']),
                'dollar_volume_75th_percentile': int(dollar_volume_desc['75%']),
                'atr': most_recent_year.atr.describe()['50%'],
            }
        # transpose the DataFrame so we have rows of tickers, and metrics as columns
        return pd.DataFrame(results).T

    def get_start_date(self, symbol):
        return self._start_dates[symbol.upper()]

    def _set_start_date(self, symbol, start_date):
        self._start_dates[symbol] = start_date

    def get_end_date(self, symbol):
        return self._end_dates[symbol.upper()]

    def _set_end_date(self, symbol, end_date):
        self._end_dates[symbol] = end_date

    def get_csv_path(self, symbol):
        return self._csv_files[symbol]

    def _set_csv_path(self, symbol, csv_path):
        self._csv_files[symbol] = csv_path

    def _get_store_contents(self):
        csv_files = [os.path.join(ZIPLINE_CACHE_DIR, f)\
                     for f in os.listdir(ZIPLINE_CACHE_DIR)\
                     if f.endswith('.csv')]
        return [self._decode_store_path(path) for path in csv_files]

    def _decode_store_path(self, csv_path):
        filename = os.path.basename(csv_path).replace('--', os.path.sep)
        symbol = filename[:filename.find('-')]

        dates = filename[len(symbol)+1:].replace('.csv', '')
        start = dates[:len(dates)/2]
        end = dates[len(dates)/2:]

        def to_dt(dt_str):
            date, time = dt_str.split(' ')
            return pd.Timestamp(' '.join([date, time.replace('-', ':')]))

        return {
            'symbol': symbol,
            'csv_path': csv_path,
            'start': to_dt(start),
            'end': to_dt(end),
        }

    def _get_store_path(self, symbol, start, end):
        '''
        :param symbol: string - the ticker
        :param start: pd.Timestamp - the earliest date
        :param end: pd.Timestamp - the latest date
        :return: string - path for the CSV
        '''
        filename_format = '%(symbol)s-%(start)s-%(end)s.csv'
        return os.path.join(ZIPLINE_CACHE_DIR, filename_format % {
            'symbol': symbol.upper().replace(os.path.sep, '--'),
            'start': start,
            'end': end,
        }).replace(':', '-')

    def _add_ta(self, df, use_adjusted=True):
        def key(price_key):
            return 'Adj ' + price_key if use_adjusted else price_key
        df['dollar_volume'] = df[key('Close')] * df.Volume
        df['atr'] = ta.NATR(df[key('High')].values, df[key('Low')].values, df[key('Close')].values) # timeperiod 14
        df['sma100'] = ta.SMA(df[key('Close')].values, timeperiod=20)
        df['sma200'] = ta.SMA(df[key('Close')].values, timeperiod=20)
        df['bbands_upper'], df['sma20'], df['bbands_lower'] = ta.BBANDS(df[key('Close')].values, timeperiod=20)
        df['macd_lead'], df['macd_lag'], df['macd_divergence'] = ta.MACD(df[key('Close')].values) # 12, 26, 9
        df['rsi'] = ta.RSI(df[key('Close')].values) # 14
        df['stoch_lead'], df['stoch_lag'] = ta.STOCH(df[key('High')].values, df[key('Low')].values, df[key('Close')].values,
                                                        fastk_period=14, slowk_period=1, slowd_period=3)
        df['slope'] = ta.LINEARREG_SLOPE(df[key('Close')].values) * -1 # talib returns the inverse of what we want
        return df
