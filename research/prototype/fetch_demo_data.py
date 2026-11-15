#!/usr/bin/env python3
"""Download the data the Signal-Origin dashboard needs (run on your own machine).

    pip install requests pandas
    python fetch_demo_data.py

Creates demo_data/ with:
  forecast_archive_gfs.csv  - GFS 2 m temperature as forecast 1-7 days ahead, Jun-Aug 2021-2026,
                              six regions (Open-Meteo Previous Runs API; for the 2021 frost replay
                              and the false-alarm count)
  kc_recent.csv             - recent Coffee C (KC=F) daily closes, for today's gauge reading
  forecast_snapshot.json    - today's 16-day forecast, used if the live feed fails during the demo
Upload the demo_data folder (or the three files) back to Claude.
"""
import json
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests

REGIONS = {  # region_id: (lat, lon) - same points as configs/v5_regions.csv
    "sul_de_minas": (-21.55, -45.43), "matas_de_minas": (-20.26, -42.03),
    "cerrado_mineiro": (-18.94, -46.99), "mogiana_sp": (-20.54, -47.40),
    "montanhas_es": (-20.33, -41.13), "planalto_ba": (-14.86, -40.84)}
OUT = Path("demo_data"); OUT.mkdir(exist_ok=True)
PREV = "https://previous-runs-api.open-meteo.com/v1/forecast"
LIVE = "https://api.open-meteo.com/v1/forecast"
HEADERS = {"User-Agent": "Mozilla/5.0 (Signal-Origin class project)"}


def get(url, params, tries=3):
    for i in range(tries):
        r = requests.get(url, params=params, headers=HEADERS, timeout=120)
        if r.status_code == 200:
            return r.json()
        last = f"HTTP {r.status_code}: {r.text[:300]}"
        time.sleep(3 * (i + 1))
    raise RuntimeError(last)


# 1) Forecast archive: what GFS predicted 1-7 days ahead, each winter 2021-2026
hourly = ["temperature_2m"] + [f"temperature_2m_previous_day{d}" for d in range(1, 8)]
rows = []
for model in ("gfs_seamless", "gfs_global"):
    try:
        for rid, (lat, lon) in REGIONS.items():
            for year in range(2021, 2027):
                j = get(PREV, {"latitude": lat, "longitude": lon, "hourly": ",".join(hourly),
                               "start_date": f"{year}-06-01", "end_date": f"{year}-08-31",
                               "models": model, "timezone": "UTC"})
                h = pd.DataFrame(j["hourly"]).assign(region_id=rid, model=model)
                rows.append(h)
                time.sleep(0.5)
            print(f"  forecast archive: {rid} done ({model})")
        break
    except Exception as e:  # try the other model name before giving up
        print(f"  model {model} failed: {e}")
        rows = []
if rows:
    pd.concat(rows).to_csv(OUT / "forecast_archive_gfs.csv", index=False)
    print("saved forecast_archive_gfs.csv")
else:
    print("!! forecast archive failed - paste the messages above to Claude")

# 2) Recent Coffee C closes (Yahoo chart endpoint; for local class use only, not for publishing)
try:
    j = get("https://query1.finance.yahoo.com/v8/finance/chart/KC=F", {"range": "2y", "interval": "1d"})
    res = j["chart"]["result"][0]
    closes = pd.DataFrame({"date": pd.to_datetime(res["timestamp"], unit="s").date,
                           "close": res["indicators"]["quote"][0]["close"]}).dropna()
    closes.to_csv(OUT / "kc_recent.csv", index=False)
    print(f"saved kc_recent.csv ({len(closes)} days, last {closes.date.iloc[-1]})")
except Exception as e:
    print(f"!! prices failed ({e}); the dashboard will use the last archived date instead")

# 3) Today's 16-day forecast as a fallback for the live demo
snap = {"fetched": str(date.today()), "regions": {}}
for rid, (lat, lon) in REGIONS.items():
    j = get(LIVE, {"latitude": lat, "longitude": lon, "daily": "temperature_2m_min,precipitation_sum",
                   "forecast_days": 16, "timezone": "UTC"})
    snap["regions"][rid] = j["daily"]
(OUT / "forecast_snapshot.json").write_text(json.dumps(snap))
print("saved forecast_snapshot.json")
