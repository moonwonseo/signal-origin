#!/usr/bin/env python3
"""Pull NASA POWER daily weather for every point in regions.csv (Signal-Origin, Celine).

Run on your own machine (POWER was not reachable from the sandbox this was written in):
    pip install requests pandas
    python pull_power_regions.py
    python pull_power_regions.py --compare-old path/to/rebuilt_daily_weather.csv

Same parameters and checks as the original Varginha pull (T2M, T2M_MAX, T2M_MIN, PRECTOTCORR;
UTC; units checked; fill values -> missing). Raw responses are saved byte-for-byte in a new
timestamped folder, so nothing earlier is ever overwritten. No features or models here.
"""
import argparse, hashlib, json, time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

API = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = {"T2M": "temperature_mean_c", "T2M_MAX": "temperature_max_c",
          "T2M_MIN": "temperature_min_c", "PRECTOTCORR": "precipitation_mm_per_day"}
UNITS = {"T2M": "C", "T2M_MAX": "C", "T2M_MIN": "C", "PRECTOTCORR": "mm/day"}
HERE = Path(__file__).resolve().parent


def request_params(lat, lon, start, end):
    return {"parameters": ",".join(PARAMS), "community": "AG",
            "latitude": lat, "longitude": lon,
            "start": start.strftime("%Y%m%d"), "end": end.strftime("%Y%m%d"),
            "format": "JSON", "time-standard": "UTC"}


def fetch(lat, lon, start, end, retries=3):
    """Return (final_url, raw_bytes). Retries politely; raises with the API message on failure."""
    last = None
    for attempt in range(retries):
        try:
            r = requests.get(API, params=request_params(lat, lon, start, end), timeout=180)
            if r.status_code == 200:
                return r.url, r.content
            last = f"HTTP {r.status_code}: {r.text[:300]}"
        except requests.RequestException as e:
            last = repr(e)
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"POWER request failed after {retries} tries -> {last}")


def parse(payload):
    """Daily DataFrame indexed by UTC date. Mirrors the V1 weather audit checks."""
    hdr = payload["header"]
    if hdr.get("time_standard") != "UTC":
        raise ValueError(f"time standard is {hdr.get('time_standard')!r}, expected 'UTC'")
    for p, unit in UNITS.items():
        got = payload["parameters"][p]["units"]
        if got != unit:
            raise ValueError(f"unexpected unit for {p}: {got!r}")
    vals = payload["properties"]["parameter"]
    days = sorted(vals["T2M"])
    df = pd.DataFrame({col: [vals[p].get(d) for d in days] for p, col in PARAMS.items()},
                      index=pd.to_datetime(days, format="%Y%m%d"), dtype=float)
    df.index.name = "weather_date_utc"
    return df.replace(hdr["fill_value"], float("nan"))


def range_problems(df):
    d = df.dropna()
    return {"negative_rain_days": int((d.precipitation_mm_per_day < 0).sum()),
            "tmin_above_tmean_days": int((d.temperature_min_c > d.temperature_mean_c).sum()),
            "tmean_above_tmax_days": int((d.temperature_mean_c > d.temperature_max_c).sum())}


def last_available(df):
    return {c: (str(df[c].last_valid_index().date()) if df[c].notna().any() else None) for c in df}


def compare_old(new_df, old_csv):
    """How much has POWER revised the Sul de Minas history since the original October pull?"""
    old = pd.read_csv(old_csv, parse_dates=["weather_date_utc"]).set_index("weather_date_utc")
    out = {}
    for c in PARAMS.values():
        both = pd.concat([old[c], new_df[c]], axis=1, keys=["old", "new"]).dropna()
        diff = (both.new - both.old).abs()
        changed = diff[diff > 0.005]
        out[c] = {"overlap_days": int(len(both)), "days_changed": int(len(changed)),
                  "max_abs_change": float(diff.max()) if len(diff) else None,
                  "earliest_changed": str(changed.index.min().date()) if len(changed) else None,
                  "latest_changed": str(changed.index.max().date()) if len(changed) else None}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", default=str(HERE.parent / "configs" / "v5_regions.csv"))
    ap.add_argument("--start", default="1981-01-01")
    ap.add_argument("--end", default=str(date.today() - timedelta(days=1)))
    ap.add_argument("--compare-old", help="original rebuilt_daily_weather.csv (Sul de Minas) for a revision check")
    a = ap.parse_args()

    regions = pd.read_csv(a.regions)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
    out = HERE / "pulls" / stamp
    (out / "raw").mkdir(parents=True)
    start, end = date.fromisoformat(a.start), date.fromisoformat(a.end)

    frames, meta = [], {"retrieved_at_utc": stamp, "api": API, "start": a.start, "end": a.end,
                        "parameters": list(PARAMS), "community": "AG", "time_standard": "UTC", "regions": {}}
    for _, r in regions.iterrows():
        print(f"pulling {r.region_id} ({r.latitude}, {r.longitude}) ...", flush=True)
        url, raw = fetch(r.latitude, r.longitude, start, end)
        (out / "raw" / f"power_{r.region_id}.json").write_bytes(raw)
        df = parse(json.loads(raw))
        meta["regions"][r.region_id] = {
            "url": url, "sha256": hashlib.sha256(raw).hexdigest(),
            "first_date": str(df.index.min().date()), "last_date_requested": str(df.index.max().date()),
            "last_available_by_variable": last_available(df),
            "missing_by_variable": {c: int(df[c].isna().sum()) for c in df},
            "range_problems": range_problems(df)}
        frames.append(df.assign(region_id=r.region_id).reset_index())
        if r.region_id == "sul_de_minas" and a.compare_old:
            meta["sul_de_minas_revisions_vs_original_pull"] = compare_old(df, a.compare_old)
        time.sleep(2)  # be gentle with the public API

    long = pd.concat(frames, ignore_index=True)
    long.to_csv(out / "power_daily_all_regions.csv", index=False)
    (out / "pull_metadata.json").write_text(json.dumps(meta, indent=2))
    print(f"done -> {out}")
    print(json.dumps({k: v["last_available_by_variable"] for k, v in meta["regions"].items()}, indent=1))
    if "sul_de_minas_revisions_vs_original_pull" in meta:
        print("revisions vs original pull:", json.dumps(meta["sul_de_minas_revisions_vs_original_pull"], indent=1))


if __name__ == "__main__":
    main()
