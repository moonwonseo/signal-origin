"""Whitelist 'other markets': one Yahoo daily series. usage: fetch_yahoo.py <ticker> <name>
Output: data/<name>.csv (date in the exchange's local calendar, close) and the raw JSON with sha256."""
import hashlib, json, sys, urllib.parse, urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd

ticker, name = sys.argv[1], sys.argv[2]
ROOT = Path(__file__).resolve().parent
url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(ticker)}?period1=946684800&period2=1791676800&interval=1d"
raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research-client)"}), timeout=60).read()
(ROOT / "data" / f"raw_yahoo_{name}.json").write_bytes(raw)
r = json.loads(raw)["chart"]["result"][0]
tz = ZoneInfo(r["meta"]["exchangeTimezoneName"])
ts = pd.to_datetime(r["timestamp"], unit="s", utc=True).tz_convert(tz)
d = pd.DataFrame({"date": ts.tz_localize(None).normalize(), "close": r["indicators"]["quote"][0]["close"]}).dropna()
d = d.drop_duplicates("date").sort_values("date")
d.to_csv(ROOT / "data" / f"{name}.csv", index=False)
print(name, ticker, r["meta"]["exchangeTimezoneName"], len(d), d.date.min().date(), d.date.max().date(), "sha256", hashlib.sha256(raw).hexdigest()[:16])
