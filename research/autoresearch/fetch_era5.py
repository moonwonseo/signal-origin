"""ERA5 daily values for the 6 Brazil nodes from the Open-Meteo archive API (ECMWF/Copernicus ERA5 reanalysis).
Output: data/era5_brazil.csv (weather_date_utc, region_id, country, tmax, tmean, rain, et0). Raw JSON kept with sha256."""
import hashlib, json, time, urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
nodes = pd.read_csv(ROOT.parent / "data" / "arabica_world_nodes.csv")
nodes = nodes[nodes.country.eq("Brazil")]
raw = ROOT / "data" / "raw_era5"; raw.mkdir(parents=True, exist_ok=True)
URL = ("https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date=1981-01-01&end_date=2026-11-05"
       "&daily=temperature_2m_max,temperature_2m_mean,precipitation_sum,et0_fao_evapotranspiration&timezone=UTC")
out, sha = [], {}
for r in nodes.itertuples():
    f = raw / f"{r.region_id}.json"
    while not f.exists():
        try:
            b = urllib.request.urlopen(urllib.request.Request(URL.format(lat=r.latitude, lon=r.longitude), headers={"User-Agent": "research-client"}), timeout=180).read()
            json.loads(b)["daily"]["time"]
            f.write_bytes(b)
        except Exception as e:
            print(r.region_id, "wait", type(e).__name__, str(e)[:80], flush=True)
            time.sleep(75)
    j = json.loads(f.read_bytes()); sha[r.region_id] = hashlib.sha256(f.read_bytes()).hexdigest()
    d = pd.DataFrame(j["daily"]).rename(columns={"time": "weather_date_utc", "temperature_2m_max": "tmax", "temperature_2m_mean": "tmean",
                                                 "precipitation_sum": "rain", "et0_fao_evapotranspiration": "et0"})
    d["region_id"], d["country"] = r.region_id, "Brazil"
    out.append(d); print(r.region_id, len(d), d.et0.notna().sum(), flush=True)
    time.sleep(70)
pd.concat(out).to_csv(ROOT / "data" / "era5_brazil.csv", index=False)
json.dump(sha, open(raw / "SHA256.json", "w"), indent=1); print("done")
