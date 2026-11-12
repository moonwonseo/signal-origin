"""Uncertainty for model comparisons when forecast windows overlap.

Daily forecasts with an h-session horizon share most of their outcome window, so rows are not
independent. We resample whole blocks of consecutive forecast dates (moving-block bootstrap,
block length = h) of the PAIRED loss difference between two models scored on the same dates.
This is a rough dependence-aware range, not a p-value or a formal significance test.

References: B0 (historical frequency) and FLAT50 (always 50%, Brier 0.25 by construction),
the simplest forecast anyone could make without data.
"""
import numpy as np
import pandas as pd

from .spec import SignalOriginError


def block_bootstrap_mean(diff: np.ndarray, block: int, n_boot: int = 2000, seed: int = 590):
    d = np.asarray(diff, dtype=float)
    n = len(d)
    if n == 0 or not np.isfinite(d).all():
        raise SignalOriginError("paired differences must be non-empty and finite")
    if type(block) is not int or block < 1:
        raise SignalOriginError("block length must be a positive integer")
    block = min(block, n)
    rng = np.random.default_rng(seed)
    starts = np.arange(n - block + 1)
    k = int(np.ceil(n / block))
    means = np.empty(n_boot)
    for b in range(n_boot):
        idx = (rng.choice(starts, k)[:, None] + np.arange(block)).ravel()[:n]
        means[b] = d[idx].mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(d.mean()), float(lo), float(hi)


def paired_brier_intervals(rows: pd.DataFrame, models, y_col: str, horizon: int,
                           n_boot: int = 2000, seed: int = 590) -> pd.DataFrame:
    """Brier gain of each model over B0 and over FLAT50 (positive = model better), with ranges."""
    rows = rows.sort_values("price_date")
    y = rows[y_col].astype(float).to_numpy()
    loss = {m: (rows["p_" + m].to_numpy(dtype=float) - y) ** 2 for m in models}
    loss["FLAT50"] = np.full(len(y), 0.25)
    out = []
    for m in models:
        for ref in ("B0", "FLAT50"):
            if m == ref or ref not in loss:
                continue
            gain, lo, hi = block_bootstrap_mean(loss[ref] - loss[m], horizon, n_boot, seed)
            out.append({"model": m, "reference": ref, "brier_gain": gain, "range_low_95": lo,
                        "range_high_95": hi, "range_excludes_zero": bool(lo > 0 or hi < 0),
                        "n_forecasts": len(y), "approx_independent_windows": round(len(y) / horizon, 1),
                        "block_length_sessions": horizon, "n_boot": n_boot, "seed": seed})
    return pd.DataFrame(out)
