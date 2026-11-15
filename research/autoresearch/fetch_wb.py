"""Whitelist 'other markets': World Bank monthly commodity prices (Pink Sheet). Output: data/wb_coffee_monthly.csv."""
import hashlib, urllib.request
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
url = "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/CMO-Historical-Data-Monthly.xlsx"
f = ROOT / "data" / "raw_wb_cmo_monthly.xlsx"      # downloaded with curl (system certificates): see run line in the journal
raw = f.read_bytes()
x = pd.read_excel(f, sheet_name="Monthly Prices", header=None)
hdr = next(i for i in range(12) if x.iloc[i].astype(str).str.contains("Coffee, Arabica").any())
cols = {str(v).strip(): j for j, v in enumerate(x.iloc[hdr]) if isinstance(v, str)}
d = x.iloc[hdr + 2:, [0, cols["Coffee, Arabica"], cols["Coffee, Robusta"]]].copy()
d.columns = ["m", "arabica", "robusta"]
d = d[d.m.astype(str).str.match(r"^\d{4}M\d{2}$")]
d["month"] = pd.to_datetime(d.m.str.replace("M", "-") + "-01")
for c in ("arabica", "robusta"):
    d[c] = pd.to_numeric(d[c], errors="coerce")
d["log_spread"] = (d.arabica / d.robusta).map(lambda v: float("nan") if not v > 0 else __import__("math").log(v))
d[["month", "arabica", "robusta", "log_spread"]].dropna().to_csv(ROOT / "data" / "wb_coffee_monthly.csv", index=False)
print(len(d), d.month.min().date(), d.month.max().date(), "sha256", hashlib.sha256(raw).hexdigest()[:16])
