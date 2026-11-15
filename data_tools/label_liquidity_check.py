"""How many V4 'spike' labels depend on thin-volume quotes or roll days? Descriptive only; no refit.
Usage: python label_liquidity_check.py <full_candidate/coffee_c_vendor_close.csv> <V4_PREDICTIONS.csv>
Primary V4 setting only: 63 sessions, delayed_180d_primary freight policy (labels are identical across models)."""
import sys, pandas as pd
prices, preds = sys.argv[1], sys.argv[2]
d = pd.read_csv(prices, parse_dates=["price_date"]).set_index("price_date")
p = pd.read_csv(preds, parse_dates=["price_date", "first_cross_date"])
q = p[(p.policy == "delayed_180d_primary") & (p.horizon == 63)].copy()
pos = q[q.target_spike == 1]
thin_first = (d.reindex(pos.first_cross_date).volume_vendor < 1000).sum()
roll_first = d.reindex(pos.first_cross_date).suspected_roll_flag.astype(bool).sum()
close, vol, where = d.close_us_cents_per_lb, d.volume_vendor, {t: i for i, t in enumerate(d.index)}
def survives(row):
    i = where[row.price_date]; c, v = close.iloc[i + 1:i + 64], vol.iloc[i + 1:i + 64]
    return c[v >= 1000].max() >= close.iloc[i] * 1.10
q["vanishes_if_thin_ignored"] = (q.target_spike == 1) & ~q.apply(survives, axis=1)
print(f"V4 63-session positives: {len(pos)} of {len(q)} forecast dates")
print(f"  first crossing on a <1,000-volume day: {thin_first}")
print(f"  first crossing on a suspected roll day: {roll_first}")
print(f"  positives that disappear if <1,000-volume closes are ignored: {int(q.vanishes_if_thin_ignored.sum())}")
print(q.groupby(q.price_date.dt.year).vanishes_if_thin_ignored.sum().rename("vanishing_positives_by_year").to_string())
