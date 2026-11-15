"""NOAA PSL Dipole Mode Index (Indian Ocean Dipole, HadISST1.1), monthly. Output: data/dmi_monthly.csv."""
import hashlib, urllib.request
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parent
raw = urllib.request.urlopen(urllib.request.Request("https://psl.noaa.gov/gcos_wgsp/Timeseries/Data/dmi.had.long.data", headers={"User-Agent": "research-client"}), timeout=60).read()
(ROOT / "data" / "raw_dmi.had.long.data").write_bytes(raw)
rows = []
for ln in raw.decode().splitlines()[1:]:
    p = ln.split()
    if len(p) == 13 and p[0].isdigit():
        rows += [(pd.Timestamp(int(p[0]), m + 1, 1), float(v)) for m, v in enumerate(p[1:]) if float(v) > -99]
d = pd.DataFrame(rows, columns=["month", "dmi"]).sort_values("month")
assert d.month.diff().dropna().dt.days.between(28, 31).all()
d.to_csv(ROOT / "data" / "dmi_monthly.csv", index=False)
print(len(d), d.month.min().date(), d.month.max().date(), "sha", hashlib.sha256(raw).hexdigest()[:16])
