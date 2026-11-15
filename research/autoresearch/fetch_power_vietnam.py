"""NASA POWER daily temperature and rain for three robusta regions of Vietnam (same layout as the main POWER file)."""
import hashlib, io, json, time, urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
NODES = {"vn_dak_lak": (12.71, 108.24), "vn_lam_dong": (11.58, 108.08), "vn_gia_lai": (13.98, 108.00)}
URL = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR&community=AG"
       "&longitude={lon}&latitude={lat}&start=19810101&end=20261113&format=CSV")
raw = ROOT / "data" / "raw_power_vietnam"; raw.mkdir(parents=True, exist_ok=True)
out, sha = [], {}
for k, (lat, lon) in NODES.items():
    f = raw / f"{k}.csv"
    if not f.exists():
        f.write_bytes(urllib.request.urlopen(urllib.request.Request(URL.format(lat=lat, lon=lon), headers={"User-Agent": "research-client"}), timeout=180).read())
        time.sleep(3)
    txt = f.read_text(); sha[k] = hashlib.sha256(txt.encode()).hexdigest()
    d = pd.read_csv(io.StringIO(txt[txt.index("-END HEADER-") + 12:].strip()))
    d["weather_date_utc"] = pd.to_datetime(d.YEAR.astype(str) + d.DOY.astype(str).str.zfill(3), format="%Y%j")
    d = d.rename(columns={"T2M": "temperature_mean_c", "T2M_MAX": "temperature_max_c", "T2M_MIN": "temperature_min_c", "PRECTOTCORR": "precipitation_mm_per_day"})
    d = d[["weather_date_utc", "temperature_mean_c", "temperature_max_c", "temperature_min_c", "precipitation_mm_per_day"]].where(lambda x: x != -999)
    d["region_id"], d["country"] = k, "Vietnam"
    assert len(d) > 16000 and d.temperature_max_c.notna().mean() > 0.99
    out.append(d); print(k, len(d), flush=True)
pd.concat(out).to_csv(ROOT / "data" / "power_vietnam.csv", index=False)
json.dump(sha, open(raw / "SHA256.json", "w"), indent=1); print("done")
