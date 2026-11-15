"""Export the data of the buyer dashboard (research/prototype). Run on the compute machine:
./run.sh export_dashboard.py

No score is calculated here. The file reads the inputs of rule c86, the saved run of `core.py final c86`
(out/c86/*_final.npy) and the rows of the trial log.

Output (out/dashboard/):
  dashboard_data.json   inputs of the rule, weekly closes, results by year, logged metrics  -> built into the page
  parity_fixture.json   sessions, harness positions and harness features                   -> tests only
Both files contain third-party rows (prices). Keep them local. Do not commit them.
"""
import json

import numpy as np
import pandas as pd

import core
import lib

CID, FIRST_YEAR, LAG, YEARS, MIN_DAYS = "c86", 2009, 10, 5, 30
OUT = core.ROOT / "out" / "dashboard"
OUT.mkdir(parents=True, exist_ok=True)

D = core.Data(core.FINAL_CUTOFF)
cand = core.load_candidate(CID)
X = cand.features(D)                                   # enso_jan, fill_tmean at each session (lag 10 days)
pos = np.load(core.ROOT / "out" / CID / "pos_final.npy")
sv = np.load(core.ROOT / "out" / CID / "saving_final.npy")
assert len(pos) == D.n == len(X)

# ---- input 1: January Nino 3.4 -------------------------------------------------------------------------
t = D.monthly("nino34")
jan = t[t.month.dt.month == 1]
enso = {int(m.year): round(float(v), 3) for m, v in zip(jan.month, jan.value) if m.year >= FIRST_YEAR - YEARS - 2}
assert (jan.avail.dt.month == 2).all() and (jan.avail.dt.day == 15).all()

# ---- input 2: Brazil mean temperature, Jan-Mar, weighted by Arabica output -----------------------------
w = pd.Series(lib.BRAZIL_W)
w = w / w.sum()
x = (D.weather_raw("temperature_mean_c")[list(w.index)] * w).sum(axis=1, skipna=False)
heat = {}
for y in range(FIRST_YEAR - YEARS - 1, int(x.index.year.max()) + 1):
    s = x[(x.index.year == y) & (x.index.month <= 3)]
    if len(s) == 0:
        continue
    assert s.notna().all() and len(s) in (90, 91), (y, len(s), int(s.isna().sum()))
    heat[y] = [round(float(v), 4) for v in s]

# ---- weekly closes (decision days) ---------------------------------------------------------------------
iso = D.dates.dt.isocalendar()
key = iso.year.astype(int) * 100 + iso.week.astype(int)
dec = (key != key.shift(-1)).to_numpy()
raw = pd.read_csv(core.DATA / "prices/coffee_c_vendor_close.csv", parse_dates=["price_date"]).set_index("price_date")
close = raw.close_us_cents_per_lb.reindex(D.dates.values).ffill().to_numpy()
m = dec & (D.dates >= f"{FIRST_YEAR - 1}-12-01").to_numpy()
weekly = [[d.strftime("%Y-%m-%d"), round(float(c), 2)] for d, c in zip(D.dates[m], close[m])]

# ---- results by calendar year (saved run) --------------------------------------------------------------
yr = D.dates.dt.year.to_numpy()
yearly = []
for y in range(FIRST_YEAR, int(yr.max()) + 1):
    k = yr == y
    e, l = float((pos[k] > 0).mean()), float((pos[k] < 0).mean())
    yearly.append(dict(year=y, saving_pct=round(float(sv[k].sum() * 100), 2),
                       cost_pct=round(float(sv[k].sum() * 12.5), 2), share_early=round(e, 3), share_late=round(l, 3),
                       state="early" if e > 0.5 else "late" if l > 0.5 else "steady", test=bool(y >= 2023)))

# ---- logged metrics ------------------------------------------------------------------------------------
rows = core.log_rows()
fin = [r for r in rows if r["kind"] == "final" and r["id"] == CID][-1]
plc = [r for r in rows if r["kind"] == "placebo" and r["id"] == CID][-1]
keep = ("ratio", "boot_lo", "boot_hi", "n_days", "years_pos", "years", "pct_cost_saved", "turnover_per_year",
        "share_early", "share_late", "hit")
metrics = dict(dev={k: fin["dev_metrics"][k] for k in keep}, test={k: fin["test_metrics"][k] for k in keep},
               passed=fin["passed"], pass_bar=0.5, needed_dev=round(core.SE0 * core.emax(fin["dev_metrics"]["N"]), 3),
               n_trials=fin["dev_metrics"]["N"], iterations=len([r for r in rows if r["kind"] == "iter"]),
               placebo=dict(n=len(plc["placebo"]), n_ge_real=plc["n_placebo_ge_real"],
                            max=max(plc["placebo"].values()), values=sorted(plc["placebo"].values())))

last = D.dates[D.usable].iloc[-1]
data = dict(
    rule=dict(id=CID, lag_days=LAG, ref_years=YEARS, min_days=MIN_DAYS, enso_avail="02-15", first_year=FIRST_YEAR,
              weights={k: round(float(v), 4) for k, v in w.items()}),
    enso_jan=enso, heat_daily=heat, weekly_close=weekly, yearly=yearly, metrics=metrics,
    price_archive_end=last.strftime("%Y-%m-%d"), weather_end=x.dropna().index.max().strftime("%Y-%m-%d"),
    sources=dict(price="Archived KC=F closes (Yahoo Finance), local use only", enso="NOAA CPC Nino 3.4 (sstoi.indices)",
                 weather="NASA POWER daily mean temperature, six Brazil Arabica regions"))
(OUT / "dashboard_data.json").write_text(json.dumps(data, separators=(",", ":")))

k = (D.dates >= f"{FIRST_YEAR - 1}-12-01").to_numpy()
fx = dict(dates=[d.strftime("%Y-%m-%d") for d in D.dates[k]], pos=[int(v) for v in pos[k]],
          no_close=[d.strftime("%Y-%m-%d") for d in D.dates[k & ~D.usable.to_numpy()]],   # not forecast dates (plan 1)
          enso_jan=[None if not np.isfinite(v) else round(float(v), 4) for v in X.enso_jan.to_numpy()[k]],
          fill_tmean=[None if not np.isfinite(v) else round(float(v), 6) for v in X.fill_tmean.to_numpy()[k]],
          yearly_saving_pct={str(r["year"]): r["saving_pct"] for r in yearly})
(OUT / "parity_fixture.json").write_text(json.dumps(fx, separators=(",", ":")))

a = X.fill_tmean.to_numpy()[k]
print("sessions", int(k.sum()), "| weekly rows", len(weekly), "| heat years", min(heat), "-", max(heat),
      "| enso years", min(enso), "-", max(enso))
print("smallest |heat anomaly| at a session:", float(np.nanmin(np.abs(a))), "| smallest |enso_jan|:",
      min(abs(v) for v in enso.values()))
print("price archive ends", data["price_archive_end"], "| weather ends", data["weather_end"])
print("states by year:", " ".join(f"{r['year']}:{r['state'][0]}" for r in yearly))
