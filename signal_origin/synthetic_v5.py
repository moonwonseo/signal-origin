"""Entirely artificial V5 inputs for software tests and the public demo path.

Prices: seeded random walk on fictional weekdays 2008-2026. Weather: six fictional regions with a
shared seasonal cycle and independent noise. Liquidity mask: seeded. NOT market or weather data.
"""
from functools import lru_cache

import numpy as np
import pandas as pd

from .io import Inputs
from .synthetic import synthetic_frames
from .weather import dry_spell_features, rebuild_features

REGIONS = ("sul_de_minas", "matas_de_minas", "cerrado_mineiro", "mogiana_sp", "montanhas_es", "planalto_ba")


@lru_cache(maxsize=1)
def _generated():
    dates = pd.bdate_range("2008-01-02", "2026-10-09")
    prices, _, metadata = synthetic_frames(len(dates), seed=5)
    values = prices.close_us_cents_per_lb.to_numpy()
    frame = pd.DataFrame({"price_date": dates, "session_index": np.arange(len(dates)),
                          "close_us_cents_per_lb": values, "model_price": values,
                          "price_usable": True, "quality_status": "ok",
                          "raw_price_text": [str(v) for v in values]})
    rng = np.random.default_rng(5905)
    days = pd.date_range("1981-01-01", "2026-10-09", freq="D")
    phase = 2 * np.pi * np.arange(len(days)) / 365.25
    long = []
    for k, region in enumerate(REGIONS):
        rain = rng.gamma(1.4, 3.0 + k * 0.2, len(days))
        rain[rng.random(len(days)) < .45] = 0
        tmean = 20 + 5 * np.sin(phase) + rng.normal(0, 2, len(days))
        long.append(pd.DataFrame({"weather_date_utc": days, "region_id": region,
                                  "temperature_mean_c": tmean, "temperature_max_c": tmean + 6,
                                  "temperature_min_c": tmean - 9 - rng.gamma(1.0, 1.0, len(days)),
                                  "precipitation_mm_per_day": rain}))
    long = pd.concat(long, ignore_index=True)
    first = long[long.region_id.eq(REGIONS[0])].set_index("weather_date_utc")
    z, _ = rebuild_features(first[["precipitation_mm_per_day", "temperature_mean_c", "temperature_min_c"]],
                            years_to_build=range(2007, 2027))
    dry = dry_spell_features(first.reset_index()[["weather_date_utc", "precipitation_mm_per_day"]])
    single = z[["rain_anom_z", "temp_anom_z"]].copy()
    single.index.name = "weather_date_utc"
    single = single.reset_index().merge(dry[["weather_observation_date", "dry_spell_max_30d"]],
                                        left_on="weather_date_utc", right_on="weather_observation_date",
                                        validate="one_to_one").drop(columns="weather_observation_date")
    liquidity = pd.Series(rng.random(len(dates)) > .35, index=frame.index, name="crossing_eligible")
    weights = pd.Series([.356, .210, .174, .139, .098, .023], index=list(REGIONS))
    metadata["notes"] += " V5 dates are fictional weekdays 2008-2026; weather regions are fictional."
    return frame, metadata, single, long, weights / weights.sum(), liquidity


def make_inputs():
    frame, metadata, single, long, weights, liquidity = _generated()
    return (Inputs(frame.copy(deep=True), dict(metadata), {"input_sha256": {}}, {}),
            single.copy(deep=True), long.copy(deep=True), weights.copy(), liquidity.copy())
