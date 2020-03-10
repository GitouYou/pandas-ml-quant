from unittest import TestCase

from pandas_ml_utils import FeaturesAndLabels
from test.config import DF_TEST
import pandas_ml_quant


print(pandas_ml_quant.__version__)


class TestExtractionOfFeaturesAndLabels(TestCase):

    def test_extract_in_rnn_shape(self):
        # implement something along the lines
        df = DF_TEST.copy()

        features, labels, weights = df.ml.extract(
            FeaturesAndLabels(
                features=[
                    lambda df: df["Close"].q.ta_rsi().q.ta_shape_for_auto_regression(280), # FIXME vorsicht das ta_shape gibt auch noch ein min required samples zurück
                    lambda df: (df["Volume"] / df["Volume"].q.ta_ema(14) - 1).q.ta_shape_for_auto_regression(280)
                ],
                labels=[
                    lambda df, forecasting_time_steps, stddevs: df["Close"].q.ta_future_multiband_bucket(forecasting_time_steps, period=14, stddevs=stddevs),
                ],
                targets=[
                    lambda df, stddevs: df["Close"].ta_multi_bbands(period=14, stddevs=stddevs),
                ]
            ),
            # kwargs
            forecasting_time_steps=7,
            stddevs=[0.5, 1.5, 2.5, 3.5]
        )

        print(features, labels, weights)

"""
    FeaturesAndLabels(
    features=["rsi", "volume"],
    labels=["future_bb"],
    sample_weights="loss_weight",
    # targets=lambda df, _, stddevs: df["Close"].ta_multi_bbands(period=14, stddevs=stddevs), # TODO rethink targets
    gross_loss=lambda df: df["gross_loss"],
    # feature_lags=range(20), # FIXME need to be part of the indicators 
    pre_processor=lambda df, forecasting_time_steps, stddevs: pmu.LazyDataFrame( # TODO rethink if preprocessor is the right thing to do
        df,
        # features
        rst             = lambda df: df["Close"].q.ta_rsi(),
        volume          = lambda df: df["Volume"] / df["Volume"].ta_ema(14) - 1,
        
        # lables 
        future_bb       = lambda df: df["Close"].ta_future_multiband_bucket(forecasting_time_steps, period=14, stddevs=stddevs),
        
        # gross loss
        gross_loss      = lambda df: df["Close"].ta_future_multiband_loss(forecasting_time_steps, period=14, stddevs=stddevs),

        # sample loss (weight)
        loss_weight     = lambda df: df["gross_loss"].abs() + 1
    ).to_dataframe()
)

"""
