"""Entirely artificial V4 inputs. No sampled or transformed third-party records."""
from functools import lru_cache

import numpy as np
import pandas as pd

from .io import Inputs
from .synthetic import synthetic_frames
from .weather import dry_spell_features, rebuild_features


@lru_cache(maxsize=1)
def _generated():
    dates = pd.bdate_range("2019-01-02", "2026-10-09")
    prices, _, metadata = synthetic_frames(len(dates), seed=42)
    values = prices.close_us_cents_per_lb.to_numpy()
    frame = pd.DataFrame({"price_date": dates, "session_index": np.arange(len(dates)),
                          "close_us_cents_per_lb": values, "model_price": values,
                          "price_usable": True, "quality_status": "ok",
                          "raw_price_text": [str(v) for v in values]})
    rng = np.random.default_rng(590)
    weather_dates = pd.date_range("1981-01-01", "2026-10-09", freq="D")
    phase = 2 * np.pi * np.arange(len(weather_dates)) / 365.25
    rain = rng.gamma(1.4, 3.0, len(weather_dates))
    rain[rng.random(len(weather_dates)) < .45] = 0
    temp = 20 + 5 * np.sin(phase) + rng.normal(0, 2, len(weather_dates))
    raw_weather = pd.DataFrame({"precipitation_mm_per_day": rain,
                                "temperature_mean_c": temp, "temperature_min_c": temp - 4},
                               index=weather_dates)
    features, _ = rebuild_features(raw_weather, years_to_build=range(2018, 2027))
    dry = dry_spell_features(pd.DataFrame({"weather_date_utc": weather_dates,
                                         "precipitation_mm_per_day": rain}))
    weather = features[["rain_anom_z", "temp_anom_z"]].copy()
    weather.index.name = "weather_date_utc"
    weather = weather.reset_index().merge(
        dry[["weather_observation_date", "dry_spell_max_30d"]], left_on="weather_date_utc",
        right_on="weather_observation_date", validate="one_to_one").drop(columns="weather_observation_date")
    month_dates = pd.date_range("2017-01-01", "2026-10-01", freq="MS")
    freight = 100 * np.exp(np.cumsum(rng.normal(.002, .035, len(month_dates))))
    monthly = pd.DataFrame({"observation_month": month_dates, "freight_ppi": freight})
    metadata["notes"] += " V4 dates are fictional weekdays; weather and freight are independently generated."
    return frame, metadata, weather, monthly


def make_inputs():
    frame, metadata, weather, monthly = _generated()
    return (Inputs(frame.copy(deep=True), dict(metadata), {"input_sha256": {}}, {}),
            weather.copy(deep=True), monthly.copy(deep=True))
