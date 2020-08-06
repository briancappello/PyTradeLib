import pandas as pd
import talib as ta

from scipy import stats


def calc_metrics(df, symbol):
    sma200 = ta.SMA(df.Close, timeperiod=200)
    slope200, *_ = stats.linregress(range(0, 10), sma200[-10:])
    rsi14 = ta.RSI(df.Close, timeperiod=14)
    new_high_over_num_bars = new_high_over_num_prior_bars(df)
    expanding_bodies, expanding_volume = expanding_bodies_and_volume(df)
    close_crossed_200 = price_crossed_sma(df)
    return pd.DataFrame.from_records([dict(
        Symbol=symbol,
        SMA200=sma200[-1],
        Slope200=slope200,
        RSI=rsi14[-1],
        NewHighOverNumBars=new_high_over_num_bars,
        ExpandingBodies=expanding_bodies,
        ExpandingVolume=expanding_volume,
        CloseCrossed200=close_crossed_200,
    )], index='Symbol')


"""
metrics df:
symbol  52w_high    52w_low     100sma(D/W/M)   200sma(D/W/M)      3month_vol      rsi

latest bar df:
symbol  open    high    low     close   volume
"""


def new_high_over_num_prior_bars(df: pd.DataFrame, col: str = "Close"):
    latest_val = df[col].iloc[-1]
    prev_val = df[col].iloc[-2]
    if latest_val < prev_val:
        return 0

    prior_high_timestamps = df.index[df[col] > latest_val]
    if prior_high_timestamps.empty:
        return len(df)

    latest_ts = df.index[-1]
    prior_high_ts = prior_high_timestamps[-1]
    num_bars = df.index.get_loc(latest_ts) - df.index.get_loc(prior_high_ts)
    return num_bars - 1  # subtract 1 to not count the latest/current bar


def expanding_bodies_and_volume(df: pd.DataFrame, num_bars: int = 3, bullish: bool = True):
    df = df[-num_bars:]
    bodies = df.Close - df.Open
    bodies_expanding = (bodies.sort_values(ascending=bullish).index == bodies.index).all()
    volume_increasing = (df.sort_values('Volume').index == df.index).all()
    return bodies_expanding, volume_increasing


def price_crossed_sma(df: pd.DataFrame, sma: int = 200, bullish: bool = True):
    """
    Whether or not the latest bar has crossed the given SMA.
    """
    if len(df) < sma:
        return False

    ma = ta.SMA(df.Close[-sma:], timeperiod=sma)[-1]
    open_ = df.Open.iloc[-1]
    close = df.Close.iloc[-1]
    prior_close = df.Close.iloc[-2]
    if bullish:
        intraday_cross = (open_ < ma) and (close > ma)
        gap_cross = (prior_close < ma) and (open_ > ma)
    else:
        intraday_cross = (open_ > ma) and (close < ma)
        gap_cross = (prior_close > ma) and (open_ < ma)
    return intraday_cross or gap_cross
