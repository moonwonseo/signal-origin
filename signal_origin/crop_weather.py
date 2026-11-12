"""V5 model A3: crop-stage weather features across the main Arabica regions.

Inputs
  * long daily weather: weather_date_utc, region_id, temperature_mean_c, temperature_max_c,
    temperature_min_c, precipitation_mm_per_day (output of data_tools/pull_power_regions.py)
  * regions CSV: region_id, weight_two_year_share (configs/v5_regions.csv)
  * crop-window spec JSON (configs/v5_crop_windows.json), fixed BEFORE any model run

Per region, using only weather dated on or before each day (no look-ahead):
  frost nights      = nights in the last 30 days with T2M_MIN below the threshold
  rain anomaly      = V4/A1's prior-years 30-day rainfall z-score (weather.rebuild_features, unchanged)
  dry spell         = V3/A2's longest dry run in the last 30 days (weather.dry_spell_features, unchanged)
  heat days (opt.)  = days in the last 30 with T2M_MAX above the threshold; only if a threshold is set
Across regions: frost uses the WORST region (frost is local; averaging is what muted 2021);
the others use production weights. Any region missing -> missing (never silently re-weighted).
Seasonal gating: each feature is its value inside its crop-stage months and 0 outside them.
Missing stays missing in every month, so gating can never make an incomplete row eligible.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from .spec import SignalOriginError
from .weather import dry_spell_features, rebuild_features

COLS = ("temperature_mean_c", "temperature_max_c", "temperature_min_c", "precipitation_mm_per_day")
BASE_FEATURES = ("a3_frost_nights_30d", "a3_flowering_rain_z", "a3_fill_dry_spell_30d")
HEAT_FEATURE = "a3_fill_heat_days_30d"


def _months(block, name):
    m = block.get("months")
    if not isinstance(m, list) or not m or any(type(x) is not int or not 1 <= x <= 12 for x in m):
        raise SignalOriginError(f"{name}.months must be a non-empty list of month numbers 1-12")
    return sorted(set(m))


def _threshold(block, name, required):
    t = block.get("threshold_c")
    if t is None and not required:
        return None
    if isinstance(t, bool) or not isinstance(t, (int, float)) or not math.isfinite(t):
        raise SignalOriginError(f"{name}.threshold_c must be a finite number" + ("" if required else " or null"))
    return float(t)


def load_crop_spec(path) -> dict:
    raw = json.loads(Path(path).read_text())
    f = raw.get("features", {})
    spec = {"frost": {"months": _months(f.get("frost_nights", {}), "frost_nights"),
                      "threshold_c": _threshold(f["frost_nights"], "frost_nights", True)},
            "rain": {"months": _months(f.get("flowering_rain_anomaly", {}), "flowering_rain_anomaly")},
            "dry": {"months": _months(f.get("grain_fill_dry_spell", {}), "grain_fill_dry_spell")}}
    heat = f.get("grain_fill_heat_days")
    if heat is not None:
        t = _threshold(heat, "grain_fill_heat_days", False)
        if t is not None:
            spec["heat"] = {"months": _months(heat, "grain_fill_heat_days"), "threshold_c": t}
    return spec


def feature_names(spec) -> tuple:
    return BASE_FEATURES + ((HEAT_FEATURE,) if "heat" in spec else ())


def load_regions(path) -> pd.Series:
    r = pd.read_csv(path)
    if not {"region_id", "weight_two_year_share"}.issubset(r) or r.region_id.duplicated().any():
        raise SignalOriginError("regions file needs unique region_id and weight_two_year_share")
    w = r.set_index("region_id").weight_two_year_share.astype(float)
    if (w <= 0).any() or abs(w.sum() - 1) > 1e-3:
        raise SignalOriginError("region weights must be positive and sum to 1")
    return w / w.sum()


def _region_daily(long: pd.DataFrame, region: str) -> pd.DataFrame:
    d = long.loc[long.region_id.eq(region), ["weather_date_utc", *COLS]].copy()
    if d.empty:
        raise SignalOriginError(f"no weather rows for region {region}")
    d["weather_date_utc"] = pd.to_datetime(d.weather_date_utc, errors="raise")
    if d.weather_date_utc.duplicated().any():
        raise SignalOriginError(f"duplicate weather dates for region {region}")
    d = d.set_index("weather_date_utc").sort_index()
    full = pd.date_range(d.index.min(), d.index.max(), freq="D")
    return d.reindex(full).astype(float)  # missing days stay missing; time is never compressed


def _rolling_count(flag: pd.Series, valid: pd.Series) -> pd.Series:
    x = flag.astype(float).where(valid)
    return x.rolling(30, min_periods=30).sum()


def _gate(values: pd.Series, months) -> pd.Series:
    """Zero outside the crop-stage months; missing stays missing."""
    outside = ~values.index.month.isin(months)
    return values.mask(outside & values.notna(), 0.0)


def crop_features(long: pd.DataFrame, weights: pd.Series, spec: dict, years_to_build=None) -> pd.DataFrame:
    missing = set(COLS) - set(long)
    if missing:
        raise SignalOriginError(f"region weather is missing columns {sorted(missing)}")
    per = {k: {} for k in ("frost", "rain", "dry", "heat")}
    for region in weights.index:
        d = _region_daily(long, region)
        per["frost"][region] = _rolling_count(d.temperature_min_c < spec["frost"]["threshold_c"],
                                              d.temperature_min_c.notna())
        z, _ = rebuild_features(d[["precipitation_mm_per_day", "temperature_mean_c", "temperature_min_c"]],
                                years_to_build=years_to_build)
        per["rain"][region] = z.rain_anom_z
        dry = dry_spell_features(pd.DataFrame({"weather_date_utc": d.index,
                                               "precipitation_mm_per_day": d.precipitation_mm_per_day.values}))
        per["dry"][region] = dry.set_index("weather_observation_date").dry_spell_max_30d.reindex(d.index)
        if "heat" in spec:
            per["heat"][region] = _rolling_count(d.temperature_max_c > spec["heat"]["threshold_c"],
                                                 d.temperature_max_c.notna())

    def weighted(parts):
        df = pd.DataFrame(parts)[weights.index]
        out = (df * weights).sum(axis=1)
        return out.where(df.notna().all(axis=1))

    frost_df = pd.DataFrame(per["frost"])[weights.index]
    out = pd.DataFrame({
        "a3_frost_nights_30d": _gate(frost_df.max(axis=1).where(frost_df.notna().all(axis=1)),
                                     spec["frost"]["months"]),
        "a3_flowering_rain_z": _gate(weighted(per["rain"]), spec["rain"]["months"]),
        "a3_fill_dry_spell_30d": _gate(weighted(per["dry"]), spec["dry"]["months"]),
    })
    if "heat" in spec:
        out[HEAT_FEATURE] = _gate(weighted(per["heat"]), spec["heat"]["months"])
    out.index.name = "weather_date_utc"
    return out.reset_index()
