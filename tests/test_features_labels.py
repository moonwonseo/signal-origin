import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest
from conftest import prepared_frame
from signal_origin.features import build_design, endpoint_labels, feature_frame
from signal_origin.io import load_inputs
from signal_origin.spec import FEATURES


@pytest.mark.parametrize("end,expected",[("110",1),("110.00",1),("109.99999999999999",0),("110.00000000000001",1),("100",0),("80",0)])
def test_inclusive_exact_threshold(end,expected):
    values=["100"]*100; values[63]=end
    label=endpoint_labels(prepared_frame(values))
    assert label.loc[0,"target_up_10pct_63_sessions"]==expected


def test_intermediate_spike_does_not_define_endpoint_event():
    values=[100]*100;values[30]=130;values[63]=105
    labels=endpoint_labels(prepared_frame(values))
    assert labels.loc[0,"target_up_10pct_63_sessions"]==0


def test_last_63_labels_missing_not_zero():
    result=endpoint_labels(prepared_frame([100]*150))
    assert result["target_up_10pct_63_sessions"].tail(63).isna().all()
    assert result["target_up_10pct_63_sessions"].iloc[:-63].eq(0).all()


def test_short_series_has_no_observed_labels():
    assert endpoint_labels(prepared_frame([100]*20))["target_up_10pct_63_sessions"].isna().all()


def test_missing_endpoint_leaves_label_unknown():
    values=[100]*100;values[63]=None
    assert pd.isna(endpoint_labels(prepared_frame(values)).loc[0,"target_up_10pct_63_sessions"])


def test_missing_future_interior_does_not_change_endpoint_horizon():
    values=[100]*100;values[30]=None;values[63]=110
    result=endpoint_labels(prepared_frame(values))
    assert result.loc[0,"target_up_10pct_63_sessions"]==1


def test_missing_source_row_does_not_shorten_63_sessions(paths):
    p=pd.read_csv(paths["prices"]);p.drop(index=10).to_csv(paths["prices"],index=False)
    inputs=load_inputs(**paths);result=endpoint_labels(inputs.frame)
    assert result.loc[0,"label_end_date"]==inputs.frame.loc[63,"price_date"]
    assert result.loc[0,"label_end_date"]!=pd.Timestamp(p.drop(index=10).iloc[63].price_date)


def test_63_sessions_not_63_calendar_days():
    frame=prepared_frame([100]*100);label=endpoint_labels(frame)
    assert (label.loc[0,"label_end_date"]-frame.loc[0,"price_date"]).days>63


def test_exact_feature_names_and_full_lookback():
    features=feature_frame(prepared_frame([100]*140))
    assert list(features.columns)==list(FEATURES)
    assert features.loc[:62,"vol63"].isna().all()
    assert features.loc[63,"vol63"]==0
    assert features.loc[63,"ret63"]==0


def test_known_return_and_sample_not_annualized_volatility():
    values=[100]*64; values[63]=110
    features=feature_frame(prepared_frame(values))
    assert features.loc[63,"ret63"]==pytest.approx(0.1)
    expected=np.std([0]*62+[0.1],ddof=1)
    assert features.loc[63,"vol63"]==pytest.approx(expected)


def test_missing_lookback_not_filled():
    values=[100]*200;values[100]=None
    f=feature_frame(prepared_frame(values))
    assert pd.isna(f.loc[120,"vol63"])
    assert pd.isna(f.loc[163,"vol63"])
    assert f.loc[164,"vol63"]==0


def test_features_unchanged_when_future_prices_change():
    frame=prepared_frame(np.arange(100,300,dtype=float))
    changed=frame.copy();changed.loc[121:,"model_price"]*=7
    pdt.assert_frame_equal(feature_frame(frame).loc[:120],feature_frame(changed).loc[:120])


def test_new_year_seasonality_and_leap_year():
    dates=pd.to_datetime(["2019-01-01","2020-01-01","2020-12-31"])
    f=feature_frame(prepared_frame([100]*3,dates))
    assert f.loc[0,"sin_doy"]==0 and f.loc[1,"sin_doy"]==0
    assert f.loc[0,"cos_doy"]==1 and f.loc[1,"cos_doy"]==1
    assert np.allclose(f.sin_doy**2+f.cos_doy**2,1)


def test_feature_engineering_never_drops_calendar_rows(inputs):
    design=build_design(inputs.frame)
    assert len(design)==len(inputs.frame)
    assert not design.loc[:62,"features_ready"].any()
    assert not design.tail(63).label_ready.any()
