from typing import Union as _Union

import numpy as _np
import pandas as _pd

import pandas_ml_quant.analysis.filters as _f
import pandas_ml_quant.analysis.indicators as _i
from pandas_ml_common import get_pandas_object as _get_pandas_object
from pandas_ml_quant.utils import index_of_bucket as _index_of_bucket

_PANDAS = _Union[_pd.DataFrame, _pd.Series]


def ta_cross_over(df: _pd.DataFrame, a=None, b=None, period=1) -> _PANDAS:
    # return only > 0
    return ta_cross(df, a, b, period).clip(lower=0)


def ta_cross_under(df: _pd.DataFrame, a=None, b=None, period=1) -> _PANDAS:
    # return only < 0
    return ta_cross(df, a, b, period).clip(upper=0)


def ta_cross(df: _pd.DataFrame, a=None, b=None, period=1):
    # get pandas objects for crossing
    if a is None and b is None:
        assert len(df.columns) == 2, f"ambiguous crossing of {df.columns}"
        a = df[df.columns[0]]
        b = df[df.columns[1]]
    elif b is None:
        b = _get_pandas_object(df, a)
        a = df
    elif a is None:
        b = _get_pandas_object(df, b)
        a = df
    else:
        a = _get_pandas_object(df, a)
        b = _get_pandas_object(df, b)

    # get periods
    a1 = a.shift(period)
    b1 = b.shift(period)

    # if a1 < b1 and a > b then a crosses over b
    a_over_b = ((a1 < b1) & (a > b)).astype(int)

    # if a1 > b1 and a < b then a cross under b
    a_under_b = ((a1 > b1) & (a < b)).astype(int) * -1

    return a_over_b + a_under_b


def ta_future_crossings(df: _PANDAS, a=None, b=None, period=1, forecast=1):
    crossings = _i.ta_cross(df, a, b, period=period)

    if forecast > 1:
        crossings = _i.ta_rnn(crossings, range(1, forecast))

    return crossings.shift(-forecast)


def ta_future_bband_quantile(df: _pd.Series, period=5, forecast_period=5, stddev=2.0, ddof=1, include_mean=True):
    # we want to know if a future price is violating the current upper/lower band
    bands = _f.ta_bbands(df, period, stddev, ddof)
    bands = bands[["lower", "mean", "upper"] if include_mean else ["lower", "upper"] ]
    future = df.shift(-forecast_period)

    return bands \
        .join(future) \
        .apply(lambda row: _index_of_bucket(row[future.name], row[bands.columns]), axis=1, raw=False) \
        .rename(f"{df.name}_quantile")


def ta_future_multi_bband_quantile(df: _pd.Series, period=5, forecast_period=5, stddevs=[0.5, 1.0, 1.5, 2.0], ddof=1, include_mean=True):
    future = df.shift(-forecast_period)
    bands = _f.ta_multi_bbands(df, period, stddevs, ddof)

    if not include_mean:
        bands = bands.drop("mean", axis=1)

    return bands \
        .join(future) \
        .apply(lambda row: _index_of_bucket(row[future.name], row[bands.columns]), axis=1, raw=False) \
        .rename(f"{df.name}_quantile")


def ta_opening_gap(df: _pd.DataFrame, offset=0.005, open="Open", close="Close"):
    gap = (df["Open"].shift(-1) / df["Close"]) - 1
    return gap.apply(lambda row: _np.nan if _np.isnan(row) or _np.isinf(row) else \
                                 2 if row > offset else 1 if row < -offset else 0)\
              .rename("opening_gap")
