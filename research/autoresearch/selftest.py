"""Checks of the harness against the Direction study code, and of the eval on synthetic positions."""
import sys
import numpy as np, pandas as pd
import core, lib
sys.path.insert(0, str(core.PROJ / "study" / "direction"))
import direction_study as ds
pos_study, load_inputs, bbm = ds._imports(core.PROJ / "repo")
pdir = core.DATA / "prices"
frame = load_inputs(pdir / "coffee_c_vendor_close.csv", pdir / "exchange_sessions.csv", pdir / "vendor_price_metadata.json").frame
base, feats, L, r, roll = ds.market_features(frame, core.DATA / "fx/usd_brl_daily.csv")
D = core.Data(core.FINAL_CUTOFF)
X = lib.market13(D)
print("market13 max abs diff vs Direction study:", float(np.nanmax(np.abs(X.to_numpy() - base[feats].to_numpy()))),
      "nan pattern equal:", bool((X.isna().to_numpy() == base[feats].isna().to_numpy()).all()), "rows", D.n, len(frame))
import direction_study2 as d2
e = d2.enso_features(core.DATA / "enso/nino34_monthly.csv", frame.price_date)
E = lib.enso2(D)
print("enso max abs diff:", float(np.nanmax(np.abs(E.to_numpy() - e.to_numpy()))), "nan equal:", bool((E.isna().to_numpy() == e.isna().to_numpy()).all()))
c = pos_study.align_cot(frame.price_date, pos_study.load_cot(core.DATA / "cftc/cftc_coffee_c_disaggregated_72hh-3qpy.csv"))
C = lib.cot2(D)
print("cot max abs diff:", float(np.nanmax(np.abs(C.to_numpy() - c[list(pos_study.POS)].to_numpy()))))
# loop-mode cut
DL = core.Data()
print("loop-mode last date:", DL.dates.max().date(), "| last label date:", DL.dates[DL.labels()[0].notna()].max().date())
y, g, end = D.labels()
t = 5000
print("label check:", bool(np.isclose(g[t], D.L[t + 1:t + 64].mean() - D.L[t])), "end:", end[t] == D.dates[t + 63])
# perfect-foresight and random positions through the eval
q = np.sign(g).fillna(0.0)
m, _ = core.metrics(core.weekly(q, D), None, D, core.DEV, 10)
print("perfect foresight of the label: RATIO %.2f, saved %.1f%%, hit %s" % (m["ratio"], m["pct_cost_saved"], m["hit"]))
rng = np.random.default_rng(1)
rs = []
for i in range(200):
    q = pd.Series(np.repeat(rng.choice([-1.0, 0.0, 1.0], size=D.n // 21 + 1), 21)[:D.n])
    rs.append(core.ratio(core.saving(core.weekly(q, D), D)[core.mask(D, core.DEV)]))
print("200 random monthly strategies: mean RATIO %.3f, sd %.3f (plan SE0 = 0.28), max %.2f; Emax(200)*0.28 = %.2f"
      % (np.mean(rs), np.std(rs, ddof=1), max(rs), 0.28 * core.emax(200)))
print("Emax 10/20/30/40:", [round(core.emax(n), 3) for n in (10, 20, 30, 40)])
