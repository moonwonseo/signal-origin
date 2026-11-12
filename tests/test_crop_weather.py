"""A3 crop-stage features: no look-ahead, seasonal gating, worst-region frost, no silent re-weighting."""
import numpy as np
import pandas as pd
import pytest

from signal_origin.crop_weather import crop_features, load_crop_spec

SPEC = load_crop_spec("configs/v5_crop_windows.json")
YEARS = range(2025, 2027)


def weather(seed=1, regions=("a", "b")):
    rng = np.random.default_rng(seed)
    days = pd.date_range("2010-01-01", "2026-06-30", freq="D")
    parts = []
    for r in regions:
        t = 20 + 5 * np.sin(2 * np.pi * np.arange(len(days)) / 365.25) + rng.normal(0, 2, len(days))
        rain = rng.gamma(1.4, 3.0, len(days)); rain[rng.random(len(days)) < .45] = 0
        parts.append(pd.DataFrame({"weather_date_utc": days, "region_id": r, "temperature_mean_c": t,
                                   "temperature_max_c": t + 6, "temperature_min_c": t - 12,
                                   "precipitation_mm_per_day": rain}))
    return pd.concat(parts, ignore_index=True)


W = pd.Series({"a": .7, "b": .3})


@pytest.fixture(scope="module")
def base():
    return crop_features(weather(), W, SPEC, YEARS).set_index("weather_date_utc")


def test_no_look_ahead(base):
    cut = pd.Timestamp("2026-02-15")
    w = weather()
    later = w.weather_date_utc > cut
    w.loc[later, ["temperature_min_c", "precipitation_mm_per_day"]] = [-20.0, 0.0]
    changed = crop_features(w, W, SPEC, YEARS).set_index("weather_date_utc")
    pd.testing.assert_frame_equal(base.loc[:cut], changed.loc[:cut])


def test_zero_outside_season(base):
    m = base.index.month
    assert (base.a3_frost_nights_30d[~m.isin([6, 7, 8])].dropna() == 0).all()
    assert (base.a3_flowering_rain_z[~m.isin([9, 10, 11])].dropna() == 0).all()
    assert (base.a3_fill_dry_spell_30d[~m.isin([1, 2, 3])].dropna() == 0).all()


def test_frost_is_worst_region_not_average():
    w = weather()
    july = w.weather_date_utc.between("2025-07-01", "2025-07-31")
    w.loc[july & w.region_id.eq("b"), "temperature_min_c"] = 0.0   # only the 30%-weight region freezes
    f = crop_features(w, W, SPEC, YEARS).set_index("weather_date_utc")
    assert f.loc["2025-07-31", "a3_frost_nights_30d"] == 30


def test_missing_region_day_is_missing_not_reweighted():
    w = weather()
    w = w[~((w.region_id == "b") & (w.weather_date_utc == "2026-01-20"))]
    f = crop_features(w, W, SPEC, YEARS).set_index("weather_date_utc")
    assert pd.isna(f.loc["2026-01-25", "a3_fill_dry_spell_30d"])
