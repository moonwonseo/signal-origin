#!/usr/bin/env python3
"""Build the optional V5 label-sensitivity mask from a local vendor price file.

Usage: python data_tools/make_liquidity_mask.py <coffee_c_vendor_close.csv> <out.csv> [--min-volume 1000]

A session is `crossing_eligible` when the vendor reported volume of at least --min-volume AND
it is not a suspected roll day. V5 uses this ONLY in its pre-declared sensitivity run: a +X%
crossing counts only on eligible days. The output contains dates and booleans, no prices.
"""
import argparse
import pandas as pd

ap = argparse.ArgumentParser()
ap.add_argument("prices"); ap.add_argument("out"); ap.add_argument("--min-volume", type=float, default=1000)
a = ap.parse_args()
d = pd.read_csv(a.prices, parse_dates=["price_date"])
vol = pd.to_numeric(d.volume_vendor, errors="coerce")
roll = d.suspected_roll_flag.astype(str).str.lower().eq("true")
out = pd.DataFrame({"price_date": d.price_date.dt.strftime("%Y-%m-%d"),
                    "crossing_eligible": (vol >= a.min_volume) & ~roll})
out.to_csv(a.out, index=False)
print(f"{out.crossing_eligible.mean():.1%} of sessions eligible for crossings -> {a.out}")
