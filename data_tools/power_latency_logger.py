#!/usr/bin/env python3
"""Measure how late NASA POWER data actually arrive, and whether recent values get revised.

Run ONCE A DAY, at roughly the same time, from today until Monday:
    python power_latency_logger.py

Each run asks for the last 60 days at two points (Sul de Minas, Cerrado Mineiro) and records:
  * latency_days  = run date minus the latest date with a real (non-fill) value, per variable
  * newly_filled  = dates that were missing last run and now have values
  * revised       = dates whose value changed since the previous run (and by how much)
Results append to latency/latency_log.csv; each run's raw response and table are kept in
latency/snapshots/. Our model currently assumes weather dated t-4 calendar days is available
on forecast day t; this log tests that assumption.
"""
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from pull_power_regions import PARAMS, fetch, parse

HERE = Path(__file__).resolve().parent
LOG_DIR = HERE / "latency"
POINTS = {"sul_de_minas": (-21.55, -45.43), "cerrado_mineiro": (-18.94, -46.99)}
WINDOW_DAYS = 60


def previous_snapshot(region):
    snaps = sorted((LOG_DIR / "snapshots").glob(f"*_{region}.csv"))
    return pd.read_csv(snaps[-1], parse_dates=["weather_date_utc"]).set_index("weather_date_utc") if snaps else None


def compare(prev, cur, col):
    if prev is None:
        return {"newly_filled": None, "revised": None, "max_abs_revision": None, "latest_revised_date": None}
    both = pd.concat([prev[col], cur[col]], axis=1, keys=["prev", "cur"]).dropna(how="all")
    filled = both[both.prev.isna() & both.cur.notna()]
    same = both.dropna()
    delta = (same.cur - same.prev).abs()
    rev = delta[delta > 0.005]
    return {"newly_filled": int(len(filled)), "revised": int(len(rev)),
            "max_abs_revision": round(float(rev.max()), 3) if len(rev) else 0.0,
            "latest_revised_date": str(rev.index.max().date()) if len(rev) else None}


def main():
    run_utc = datetime.now(timezone.utc)
    stamp = run_utc.strftime("%Y%m%dT%H%M%SZ")
    (LOG_DIR / "snapshots").mkdir(parents=True, exist_ok=True)
    today = run_utc.date()
    start, end = today - timedelta(days=WINDOW_DAYS), today  # ask up to today; missing days come back as fill values

    rows = []
    for region, (lat, lon) in POINTS.items():
        try:
            url, raw = fetch(lat, lon, start, end)
        except Exception as e:  # keep a record of failed runs too
            rows.append({"run_utc": stamp, "region_id": region, "variable": "ALL", "error": str(e)[:300]})
            continue
        cur = parse(json.loads(raw))
        prev = previous_snapshot(region)
        (LOG_DIR / "snapshots" / f"{stamp}_{region}.json").write_bytes(raw)
        cur.to_csv(LOG_DIR / "snapshots" / f"{stamp}_{region}.csv")
        for col in PARAMS.values():
            last = cur[col].last_valid_index()
            rows.append({"run_utc": stamp, "region_id": region, "variable": col,
                         "last_available_date": str(last.date()) if last is not None else None,
                         "latency_days": (today - last.date()).days if last is not None else None,
                         **compare(prev, cur, col), "error": None})

    log = LOG_DIR / "latency_log.csv"
    new = pd.DataFrame(rows)
    (pd.concat([pd.read_csv(log), new]) if log.exists() else new).to_csv(log, index=False)
    print(new.drop(columns=["error"]).to_string(index=False) if new.error.isna().all() else new.to_string(index=False))
    print(f"\nlogged -> {log}")


if __name__ == "__main__":
    main()
