"""Does weather help forecast Coffee C price volatility? Local exploratory study (see PLAN.md).

Reads (never writes) the signal_origin package and local data. All features use information
available at forecast date t: prices through t, weather dated t-4 calendar days.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from signal_origin.uncertainty import block_bootstrap_mean
from signal_origin.v5_labels import threshold_labels

HERE = Path(__file__).resolve().parent
PRICE_FEATS = ("lrv5", "lrv21", "lrv63", "sin_doy", "cos_doy")
SINGLE = ("rain_anom_z", "temp_anom_z")
A3 = ("a3_frost_nights_30d", "a3_flowering_rain_z", "a3_fill_dry_spell_30d")
MODELS = {"V1": PRICE_FEATS, "W1": PRICE_FEATS + SINGLE, "W3": PRICE_FEATS + A3}
FLOOR = 1e-6  # guards log(0) for a window of identical closes; count reported


def log_returns(frame: pd.DataFrame) -> pd.Series:
    p = frame.model_price.astype(float).where(frame.price_usable)
    return np.log(p).diff()                      # r_t uses closes t-1 and t; NaN if either missing


def trailing_rv(r: pd.Series, n: int) -> pd.Series:
    """Std of returns t-n+1..t (needs all n). Uses information through t only."""
    return r.rolling(n, min_periods=n).std(ddof=1)


def future_rv(r: pd.Series, h: int) -> pd.Series:
    """Std of returns t+1..t+h (needs all h): the forecast target, never a feature."""
    return r[::-1].rolling(h, min_periods=h).std(ddof=1)[::-1].shift(-1)


def build(frame, single, crop, h, lag_days=4):
    r = log_returns(frame)
    d = frame[["price_date"]].copy()
    floors = {}
    for n in (5, 21, 63):
        rv = trailing_rv(r, n)
        floors[f"rv{n}"] = int((rv == 0).sum())
        d[f"lrv{n}"] = np.log(rv.clip(lower=FLOOR))
    d["rv63"] = trailing_rv(r, 63)
    frv = future_rv(r, h)
    floors["future"] = int((frv == 0).sum())
    d["target"] = np.log(frv.clip(lower=FLOOR))
    d["label_end_date"] = frame.price_date.shift(-h)
    phase = (d.price_date.dt.dayofyear - 1) / np.where(d.price_date.dt.is_leap_year, 366.0, 365.0)
    d["sin_doy"], d["cos_doy"] = np.sin(2 * np.pi * phase), np.cos(2 * np.pi * phase)
    d["weather_observation_date"] = d.price_date - pd.Timedelta(days=lag_days)
    w = single[["weather_date_utc", *SINGLE]].merge(crop, on="weather_date_utc", how="outer")
    d = d.merge(w, left_on="weather_observation_date", right_on="weather_date_utc", how="left",
                validate="many_to_one")
    d.index = frame.index
    cols = sorted({c for m in MODELS.values() for c in m} | {"target", "rv63"})
    d["eligible"] = np.isfinite(d[cols].to_numpy(float)).all(axis=1)
    return d, floors


def fit_predict(train, test, feats, alpha=1.0):
    m = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=alpha))])
    m.fit(train[list(feats)], train.target)
    resid_var = float(np.var(train.target - m.predict(train[list(feats)]), ddof=1))
    coefs = dict(zip(feats, m.named_steps["ridge"].coef_.round(4)))
    return m.predict(test[list(feats)]), resid_var, coefs


def run_folds(d, years, train_start="2008-01-02"):
    preds, coefs = [], {}
    for y in years:
        dates = d.price_date[d.price_date.dt.year.eq(y)]
        start, end = dates.min(), dates.max()
        tr = d[d.eligible & (d.price_date >= pd.Timestamp(train_start)) & (d.label_end_date < start)]
        te = d[d.eligible & d.price_date.between(start, end)].copy()
        if tr.label_end_date.max() >= start:
            raise AssertionError("training outcome overlaps test year")
        te["fold_year"] = y
        te["pred_V0"] = te.lrv63
        te["sigma_V0"] = te.rv63
        for name, feats in MODELS.items():
            p, rv, c = fit_predict(tr, te, feats)
            te["pred_" + name] = p
            te["sigma_" + name] = np.exp(p + rv / 2)    # bias-corrected daily vol forecast
            coefs[f"{name}/{y}"] = c
        preds.append(te)
    return pd.concat(preds), coefs


def gauge(sigma, k, h):
    return np.clip(2 * (1 - norm.cdf(np.log(1 + k / 100) / (sigma * np.sqrt(h)))), 0, 1)


SCOPES = {"all_2012_2026": (2012, 2026), "2012_2018": (2012, 2018), "2019_onward": (2019, 2026)}


def compare(p, a, b, loss_a, loss_b, h, scope_rows):
    la, lb = loss_a(scope_rows), loss_b(scope_rows)
    g, lo, hi = block_bootstrap_mean((la - lb).to_numpy(float), int(h), 2000, 590)
    return dict(model=b, reference=a, gain=g, low=lo, high=hi)


def main(prices_dir, weather_features, region_weather, out):
    from signal_origin.crop_weather import crop_features, load_crop_spec, load_regions
    from signal_origin.io import load_inputs
    repo = Path(__import__("signal_origin").__file__).resolve().parents[1]
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    inp = load_inputs(Path(prices_dir) / "coffee_c_vendor_close.csv", Path(prices_dir) / "exchange_sessions.csv",
                      Path(prices_dir) / "vendor_price_metadata.json")
    frame = inp.frame
    single = pd.read_csv(weather_features, parse_dates=["weather_date_utc"])
    crop_path = out / "a3_features.csv"
    if crop_path.exists():
        crop = pd.read_csv(crop_path, parse_dates=["weather_date_utc"])
    else:
        crop = crop_features(pd.read_csv(region_weather), load_regions(repo / "configs/v5_regions.csv"),
                             load_crop_spec(repo / "configs/v5_crop_windows.json"), years_to_build=range(2007, 2027))
        crop.to_csv(crop_path, index=False)
    years = list(range(2012, 2027))
    vol_rows, gauge_rows, all_preds, all_coefs, floors_all = [], [], [], {}, {}
    for h in (63, 21):
        d, floors = build(frame, single, crop, h)
        floors_all[h] = floors
        p, coefs = run_folds(d, years)
        all_coefs[h] = coefs
        p["h"] = h
        all_preds.append(p)
        # 1) volatility forecast accuracy (squared error of log RV)
        for scope, (lo, hi) in SCOPES.items():
            s = p[p.fold_year.between(lo, hi)]
            for ref, mod in [("V0", "V1"), ("V1", "W1"), ("V1", "W3"), ("V0", "W3")]:
                r = compare(p, ref, mod, lambda x, m=ref: (x["pred_" + m] - x.target) ** 2,
                            lambda x, m=mod: (x["pred_" + m] - x.target) ** 2, h, s)
                r["oos_r2_vs_ref"] = 1 - ((s["pred_" + mod] - s.target) ** 2).mean() / ((s["pred_" + ref] - s.target) ** 2).mean()
                vol_rows.append(dict(h=h, scope=scope, n=len(s), **r))
            for q in (1, 2, 3, 4):
                sq = s[s.price_date.dt.quarter.eq(q)]
                r = compare(p, "V1", "W3", lambda x: (x.pred_V1 - x.target) ** 2,
                            lambda x: (x.pred_W3 - x.target) ** 2, h, sq)
                vol_rows.append(dict(h=h, scope=f"{scope}_Q{q}", n=len(sq), **r))
        # 2) product test: gauges vs B0 on V5's spike labels
        for k in (5, 10, 15):
            lab = threshold_labels(frame, h, k)
            q = p.join(lab[["target_spike"]]).dropna(subset=["target_spike"])
            q = q.assign(y=q.target_spike.astype(float))
            for y in years:  # B0: training-label frequency, purged exactly like V5
                start = q.price_date[q.fold_year.eq(y)].min()
                tr = lab.target_spike[(frame.price_date >= pd.Timestamp("2008-01-02")) &
                                      (frame.price_date.shift(-h) < start) & lab.target_spike.notna()]
                q.loc[q.fold_year.eq(y), "g_B0"] = float(tr.astype(float).mean())
            for m in ("V0", "V1", "W1", "W3"):
                q["g_" + m] = gauge(q["sigma_" + m].to_numpy(), k, h)
            for scope, (lo, hi) in SCOPES.items():
                s = q[q.fold_year.between(lo, hi)]
                for m in ("B0", "V0", "V1", "W1", "W3"):
                    row = dict(k=k, h=h, scope=scope, model=m, n=len(s), event_rate=s.y.mean(),
                               mean_prob=s["g_" + m].mean(), brier=((s["g_" + m] - s.y) ** 2).mean())
                    for ref in ("B0", "V0"):
                        if ref != m:
                            r = compare(s, ref, m, lambda x, rr=ref: (x["g_" + rr] - x.y) ** 2,
                                        lambda x, mm=m: (x["g_" + mm] - x.y) ** 2, h, s)
                            row.update({f"gain_vs_{ref}": r["gain"], f"low_vs_{ref}": r["low"], f"high_vs_{ref}": r["high"]})
                    gauge_rows.append(row)
    pd.DataFrame(vol_rows).to_csv(out / "volatility_accuracy.csv", index=False)
    pd.DataFrame(gauge_rows).to_csv(out / "gauge_brier.csv", index=False)
    pd.concat(all_preds).to_csv(out / "predictions.csv", index=False)
    json.dump(all_coefs, open(out / "coefficients.json", "w"), indent=1, default=float)
    json.dump({"plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest(),
               "zero_variance_windows_floored": floors_all,
               "note": "Local exploratory study; not part of the repo or the V5 sign-off."},
              open(out / "RECEIPT.json", "w"), indent=1)


if __name__ == "__main__":
    main(*sys.argv[1:5])
