"""Whitelist source 1: NASA POWER daily humidity, root-zone soil moisture, solar radiation for the 37 nodes.
Output: data/power_extra.csv (same layout as the main POWER file) and raw files with sha256 in data/raw_power_extra/."""
import hashlib, io, json, sys, time, urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
nodes = pd.read_csv(ROOT.parent / "data" / "arabica_world_nodes.csv")
raw_dir = ROOT / "data" / "raw_power_extra"
raw_dir.mkdir(parents=True, exist_ok=True)
URL = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=RH2M,GWETROOT,ALLSKY_SFC_SW_DWN&community=AG"
       "&longitude={lon}&latitude={lat}&start=19810101&end=20261113&format=CSV")
out, shas = [], {}
for r in nodes.itertuples():
    f = raw_dir / f"{r.region_id}.csv"
    if not f.exists():
        for attempt in range(4):
            try:
                req = urllib.request.Request(URL.format(lon=r.longitude, lat=r.latitude), headers={"User-Agent": "research-client"})
                f.write_bytes(urllib.request.urlopen(req, timeout=120).read())
                break
            except Exception as e:
                print(r.region_id, "retry", attempt, type(e).__name__, flush=True)
                time.sleep(10)
    txt = f.read_text()
    shas[r.region_id] = hashlib.sha256(txt.encode()).hexdigest()
    d = pd.read_csv(io.StringIO(txt[txt.index("-END HEADER-") + len("-END HEADER-"):].strip()))
    d["weather_date_utc"] = pd.to_datetime(d.YEAR.astype(str) + d.DOY.astype(str).str.zfill(3), format="%Y%j") if "DOY" in d \
        else pd.to_datetime(dict(year=d.YEAR, month=d.MO, day=d.DY))
    d = d.rename(columns={"RH2M": "rh2m", "GWETROOT": "gwetroot", "ALLSKY_SFC_SW_DWN": "srad"})
    d = d[["weather_date_utc", "rh2m", "gwetroot", "srad"]].where(lambda x: x != -999)
    d["region_id"], d["country"] = r.region_id, r.country
    out.append(d)
    print(r.region_id, len(d), d.gwetroot.notna().sum(), flush=True)
pd.concat(out).to_csv(ROOT / "data" / "power_extra.csv", index=False)
json.dump(shas, open(raw_dir / "SHA256.json", "w"), indent=1)
print("done")
