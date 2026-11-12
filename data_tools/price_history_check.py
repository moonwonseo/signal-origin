"""Celine's 2000-2018 price-history check (descriptive only; no model fitting).
Input: full_candidate/coffee_c_vendor_close.csv from the V4 archive (raw vendor closes, proxy calendar).
Eligibility mirrors the existing pipeline: origin priced, complete 64-price trailing window
(63 returns for ret63/vol63) and complete 63-session forward window."""
import sys, numpy as np, pandas as pd
src = sys.argv[1] if len(sys.argv) > 1 else "coffee_c_vendor_close.csv"  # full_candidate file from the V4 archive
d = pd.read_csv(src, parse_dates=["price_date"]).sort_values("price_date").reset_index(drop=True)
p = d.close_us_cents_per_lb.to_numpy(float); n = len(p); H, T = 63, 64
priced = ~np.isnan(p)

def eligible(lo, hi):
    """Origins in [lo,hi) index range whose trailing/forward windows stay inside [lo,hi) and are fully priced."""
    ok = np.zeros(n, bool)
    for i in range(lo + T - 1, hi - H):
        if priced[i - T + 1:i + 1].all() and priced[i + 1:i + H + 1].all():
            ok[i] = True
    return ok

def crossing(i, thr=0.10):
    return float(np.nanmax(p[i + 1:i + H + 1]) >= p[i] * (1 + thr))

# Sanity check against the reviewed 2019+ sample (Moonwon's review: 1,829 origins)
lo19 = int(np.searchsorted(d.price_date, pd.Timestamp("2019-01-02")))
print("check: eligible origins, 2019+ sample only =", int(eligible(lo19, n).sum()), "(expected 1829)")

ok = eligible(0, n)
d["eligible"] = ok
d["event10_63"] = [crossing(i) if ok[i] else np.nan for i in range(n)]
d["ret1"] = np.log(d.close_us_cents_per_lb).diff()
d["year"] = d.price_date.dt.year
d["stale3"] = (d.close_us_cents_per_lb.diff() == 0) & (d.close_us_cents_per_lb.diff().shift() == 0)
big = d[(d.ret1.abs() > 0.08) & ~d.suspected_roll_flag.astype(bool)]

g = d.groupby("year")
out = pd.DataFrame({
    "sessions": g.size(),
    "blank_prices": g.close_us_cents_per_lb.apply(lambda s: int(s.isna().sum())),
    "suspected_rolls": g.suspected_roll_flag.apply(lambda s: int(s.astype(bool).sum())),
    "low_volume_share": g.liquidity_flag.apply(lambda s: round((s != "source_volume_at_least_1000").mean(), 2)),
    "stale_3day_runs": g.stale3.sum().astype(int),
    "big_nonroll_moves_gt8pct": big.groupby("year").size(),
    "eligible_origins": g.eligible.sum().astype(int),
    "event_rate_10pct_within_63": g.event10_63.mean().round(3),
}).fillna(0)
pd.set_option("display.width", 200)
print(out.to_string())
print("\nBlank-price dates 2000-2018:", d[(d.year <= 2018) & d.close_us_cents_per_lb.isna()].price_date.dt.date.tolist())
print("\nBig non-roll daily moves (>8%):"); print(big[["price_date", "close_us_cents_per_lb", "ret1", "volume_vendor"]].to_string(index=False))
pre = d[(d.year <= 2018)]
print(f"\nEligible origins 2000-2018: {int(pre.eligible.sum())} | 2008-2018: {int(pre[pre.year>=2008].eligible.sum())} | 2019+: {int(d[d.year>=2019].eligible.sum())}")
out.to_csv("price_history_check_by_year.csv")
print("\nwrote price_history_check_by_year.csv")
