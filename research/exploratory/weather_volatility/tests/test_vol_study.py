"""Leakage and construction checks on artificial data."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import vol_study as vs
from signal_origin.synthetic_v4 import make_inputs


@pytest.fixture(scope="module")
def data():
    inp, weather, _ = make_inputs()
    frame = inp.frame
    days = pd.date_range("2015-01-01", "2026-12-31", freq="D")
    rng = np.random.default_rng(1)
    crop = pd.DataFrame({"weather_date_utc": days, **{c: rng.normal(size=len(days)) for c in vs.A3}})
    single = weather.assign(weather_date_utc=pd.to_datetime(weather.weather_date_utc))
    return frame, single, crop


def test_future_rv_is_exactly_next_h_returns(data):
    frame = data[0]
    r = vs.log_returns(frame); f = vs.future_rv(r, 21)
    i = 500
    assert np.isclose(f.iloc[i], r.iloc[i + 1:i + 22].std(ddof=1))


def test_features_ignore_the_future_and_target_ignores_the_past(data):
    frame, single, crop = data
    d0, _ = vs.build(frame, single, crop, 63)
    t = 1000
    fut = frame.copy(); fut.loc[t + 1:, "model_price"] *= np.linspace(1, 3, len(fut) - t - 1)
    d1, _ = vs.build(fut, single, crop, 63)
    feats = list(vs.PRICE_FEATS + vs.SINGLE + vs.A3)
    pd.testing.assert_frame_equal(d0.loc[:t, feats], d1.loc[:t, feats])
    past = frame.copy(); past.loc[:t - 1, "model_price"] *= 1.7
    d2, _ = vs.build(past, single, crop, 63)
    assert np.allclose(d0.loc[t:t + 200, "target"], d2.loc[t:t + 200, "target"], equal_nan=True)


def test_weather_joined_at_t_minus_4(data):
    frame, single, crop = data
    d, _ = vs.build(frame, single, crop, 63)
    assert (d.weather_observation_date == d.price_date - pd.Timedelta(days=4)).all()
    row = d.dropna(subset=["a3_frost_nights_30d"]).iloc[10]
    src = crop.set_index("weather_date_utc").loc[row.price_date - pd.Timedelta(days=4), "a3_frost_nights_30d"]
    assert row.a3_frost_nights_30d == src


def test_folds_are_purged(data):
    frame, single, crop = data
    d, _ = vs.build(frame, single, crop, 63)
    p, _ = vs.run_folds(d, [2024, 2025], train_start="2019-01-02")
    assert set(p.fold_year) == {2024, 2025} and p.pred_W3.notna().all()


def test_gauge_behaves():
    s = np.array([0.01, 0.02, 0.03])
    g = vs.gauge(s, 10, 63)
    assert (np.diff(g) > 0).all() and ((g >= 0) & (g <= 1)).all()
