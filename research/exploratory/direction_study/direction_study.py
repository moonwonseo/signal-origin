"""Direction of Coffee C returns (up or down), with and without weather. See PLAN.md (Direction_PLAN.md).

Usage:
  python direction_study.py --repo <signal-origin checkout> --prices <full_candidate dir> --fx <usd_brl_daily.csv>
      --weather <power_daily_arabica_world.csv> --nodes <arabica_world_nodes.csv> --z <dir with rain_z.csv,
      temp_z.csv built from 1991> --plan <PLAN.md> --out <dir> [--jobs N] [--smoke] [--placebo-shift-years K]

No leakage: prices through t, USD/BRL through t-1, weather at t-4 calendar days; scalers, calibration and models
fit on training rows only; training outcomes end before the test year.
"""
import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

ap = argparse.ArgumentParser()
for a in ("repo", "prices", "fx", "weather", "nodes", "z", "plan", "out"):
    ap.add_argument("--" + a, required=True)
ap.add_argument("--jobs", type=int, default=-1)
ap.add_argument("--smoke", action="store_true", help="tiny run to test the code; prints no metrics")
ap.add_argument("--placebo-shift-years", type=int, default=0)
ARGS = ap.parse_args() if __name__ == "__main__" else None

LAG, COST = 4, 0.0005
HS = (5, 21)
SEEDS = (590, 591, 592, 593, 594)
XGB = dict(n_estimators=300, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.5,
           min_child_weight=20, reg_lambda=1.0, tree_method="hist", n_jobs=1)
BRAZIL_W = {"sul_de_minas": 0.3561, "matas_de_minas": 0.2102, "cerrado_mineiro": 0.1739, "mogiana_sp": 0.1391,
            "montanhas_es": 0.0975, "planalto_ba": 0.0231}
SCOPES = {"all_2012_2026": (2012, 2026), "2012_2018": (2012, 2018), "2019_onward": (2019, 2026)}
PLACEBO_WINDOW_START = "1996-01-02"


def _imports(repo):
    repo = Path(repo)
    for sub in ("", "research/exploratory/cftc_positioning", "research/exploratory/weather_volatility"):
        sys.path.insert(0, str(repo / sub))
    import pos_study
    from signal_origin.io import load_inputs
    from signal_origin.uncertainty import block_bootstrap_mean
    return pos_study, load_inputs, block_bootstrap_mean


def market_features(frame, fx_csv):
    """Roll-adjusted log price L (missing closes carried forward) and the 13 market features."""
    d = frame[["price_date"]].copy()
    px = frame.model_price.astype(float).where(frame.price_usable).ffill()
    r = np.log(px).diff()
    roll = frame.suspected_roll_flag.astype(str).str.lower().eq("true")
    if os.environ.get("ROLL_FIX") == "1":          # repair of 15 Nov 2026: the contract gap is in the NEXT session
        roll = roll | roll.shift(1, fill_value=False)
    r = r.where(~roll, 0.0)
    L = r.fillna(0.0).cumsum()
    L[px.isna()] = np.nan
    for n in (5, 21, 63, 126, 252):
        d[f"kret{n}"] = L - L.shift(n)
    for n in (21, 63):
        d[f"lrv{n}"] = np.log(r.rolling(n, min_periods=n).std(ddof=1).clip(lower=1e-6))
    phase = (d.price_date.dt.dayofyear - 1) / np.where(d.price_date.dt.is_leap_year, 366.0, 365.0)
    d["sin_doy"], d["cos_doy"] = np.sin(2 * np.pi * phase), np.cos(2 * np.pi * phase)
    fx = pd.read_csv(fx_csv, parse_dates=["date"]).sort_values("date")
    fx["lfx"] = np.log(fx.usd_brl_close.astype(float))
    m = pd.merge_asof(d[["price_date"]], fx[["date", "lfx"]], left_on="price_date", right_on="date",
                      direction="backward", allow_exact_matches=False, tolerance=pd.Timedelta(days=7))
    assert (m.date.dropna() < m.price_date[m.date.notna()]).all()      # USD/BRL strictly before t
    lfx = pd.Series(m.lfx.to_numpy(), index=d.index)
    for n in (5, 21, 63):
        d[f"brl_ret{n}"] = lfx - lfx.shift(n)
    d["brl_lrv21"] = np.log(lfx.diff().rolling(21, min_periods=21).std(ddof=1).clip(lower=1e-6))
    feats = [c for c in d.columns if c != "price_date"]
    return d, feats, L, r, roll


def weather_features(weather_csv, nodes_csv, zdir, price_dates, shift_years=0):
    rain = pd.read_csv(Path(zdir) / "rain_z.csv", index_col=0, parse_dates=True)
    temp = pd.read_csv(Path(zdir) / "temp_z.csv", index_col=0, parse_dates=True)
    nodes = pd.read_csv(nodes_csv).set_index("region_id")
    assert sorted(rain.columns) == sorted(nodes.index) == sorted(temp.columns)
    w = pd.Series(BRAZIL_W) / sum(BRAZIL_W.values())
    out, b1, b2 = {}, [], []
    for c, ids in nodes.groupby("country").groups.items():
        tag = c.lower()[:3]
        for nm, z in (("rain", rain), ("temp", temp)):
            if c == "Brazil":
                m = (z[list(w.index)] * w).sum(axis=1, skipna=False)
            else:
                m = z[list(ids)].mean(axis=1, skipna=False)
            cols = {f"w_{nm}_lvl_{tag}": m - m.rolling(1825, min_periods=1825).mean(),
                    f"w_{nm}_d5_{tag}": m.diff(5), f"w_{nm}_d21_{tag}": m.diff(21)}
            out.update(cols)
            (b1 if c == "Brazil" else b2).extend(cols)
            if c == "Brazil" and nm == "rain":
                bra_rain = m
    d = pd.read_csv(weather_csv, parse_dates=["weather_date_utc"],
                    usecols=["weather_date_utc", "region_id", "country", "temperature_min_c"])
    tmin = (d[d.country.eq("Brazil")].pivot(index="weather_date_utc", columns="region_id",
                                            values="temperature_min_c").min(axis=1, skipna=False))
    tmin = tmin.reindex(rain.index)
    mon = pd.Series(rain.index.month, index=rain.index)
    frost = (5.0 - tmin.rolling(5, min_periods=5).min()).clip(lower=0).where(mon.isin([6, 7, 8]), 0.0)
    out["w_frost_depth_bra"] = frost
    out["w_frost_d21_bra"] = frost.diff(21)
    out["w_flower_rain_bra"] = bra_rain.where(mon.isin([9, 10, 11]), 0.0)
    out["w_fill_rain_bra"] = bra_rain.where(mon.isin([1, 2, 3]), 0.0)
    b1 += ["w_frost_depth_bra", "w_frost_d21_bra", "w_flower_rain_bra", "w_fill_rain_bra"]
    wx = pd.DataFrame(out)
    if shift_years:                                 # placebo: rotate whole years inside the complete window
        x = wx.loc[PLACEBO_WINDOW_START:]
        wx = pd.DataFrame(np.roll(x.to_numpy(), shift_years * 365, axis=0), index=x.index, columns=x.columns)
    al = wx.reindex((price_dates - pd.Timedelta(days=LAG)).values)
    al.index = price_dates.index
    return al, b1, b2


def xgb_calibrated(xtr, ytr, xte, seeds, params):
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.model_selection import KFold
    from xgboost import XGBClassifier
    p = np.zeros(len(xte))
    for s in seeds:
        m = CalibratedClassifierCV(XGBClassifier(**params, random_state=s), method="sigmoid",
                                   cv=KFold(3, shuffle=False), ensemble=True)
        p += m.fit(xtr, ytr).predict_proba(xte)[:, 1]
    return p / len(seeds)


def run_fold(y, D):
    e, dates, sets = D["base"], D["dates"], D["sets"]
    yd = dates[dates.dt.year.eq(y)]
    start, end = yd.min(), yd.max()
    allf = sorted({f for fs in sets.values() for f in fs})
    ok = np.isfinite(e[allf].to_numpy(float)).all(axis=1) & D["usable"]
    in_year = dates.between(start, end).to_numpy()
    res = []
    for h in D.get("hs", HS):                        # horizons travel with the data to parallel workers
        fwd = D["fwd"][h]
        lab_end = dates.shift(-h)
        trm = ok & fwd.notna().to_numpy() & (lab_end < start).to_numpy()
        tr, te = e[trm], e[ok & in_year]
        assert lab_end[tr.index].max() < start
        ytr = (fwd[tr.index] > 0).astype(int).to_numpy()
        o = te[["price_date"]].copy()
        o["h"], o["fold_year"], o["fwd"], o["n_train"] = h, y, fwd[te.index], len(tr)
        o["p_B0"] = ytr.mean()
        o["mom_up"] = (te.kret63 > 0).astype(float)
        for s, f in sets.items():
            o[f"p_XGB_{s}"] = xgb_calibrated(tr[f].to_numpy(float), ytr, te[f].to_numpy(float), D["seeds"], D["xgb"])
            o[f"p_LIN_{s}"] = D["clf"]().fit(tr[f], ytr).predict_proba(te[f])[:, 1]
        res.append(o)
    return pd.concat(res)


def evaluate(pred, frame, r, bbm, models):
    from sklearn.metrics import roc_auc_score
    dates, nxt = frame.price_date, r.shift(-1)
    rows = []
    for h, p in pred.groupby("h"):
        up = {m: (p["p_" + m] > 0.5) for m in [*models, "B0"]}
        up["ALWAYS_UP"] = pd.Series(True, index=p.index)
        up["MOM"] = p.mom_up > 0.5
        pnl = {}
        for m, u in up.items():
            sig = pd.Series(np.nan, index=frame.index)
            sig[p.index] = np.where(u, 1.0, -1.0)
            pos = sig.rolling(h, min_periods=1).mean().fillna(0.0)
            pnl[m] = pos * nxt - COST * pos.diff().abs().fillna(0.0)
        live = pd.Series(False, index=frame.index)
        live[p.index] = True
        live &= nxt.notna()
        for scope, (lo, hi) in SCOPES.items():
            s = p[p.fold_year.between(lo, hi) & p.fwd.notna()]
            if not len(s):
                continue
            y = (s.fwd > 0).to_numpy()
            msk = (live & dates.dt.year.between(lo, hi)).to_numpy()
            hit = {m: (u[s.index].to_numpy() == y).astype(float) for m, u in up.items()}
            ll = lambda q: -(y * np.log(np.clip(q, 1e-6, 1 - 1e-6)) + (~y) * np.log(np.clip(1 - q, 1e-6, 1 - 1e-6)))
            for m in up:
                g, a, b = bbm(hit[m] - 0.5, int(h), 2000, 590)
                x = pnl[m].to_numpy(float)[msk]
                pg, pa, pb = bbm(x, int(h), 2000, 590)
                row = dict(h=h, scope=scope, model=m, n=len(s), windows=round(len(s) / h), up_rate=y.mean(),
                           hit=g + 0.5, hit_low=a + 0.5, hit_high=b + 0.5, pred_up_share=up[m][s.index].mean(),
                           pnl_ann=pg * 252, pnl_low=pa * 252, pnl_high=pb * 252,
                           sharpe=x.mean() / x.std(ddof=1) * np.sqrt(252) if x.std() > 0 else np.nan)
                if m != "ALWAYS_UP":
                    g, a, b = bbm(hit[m] - hit["ALWAYS_UP"], int(h), 2000, 590)
                    row.update(hit_vs_up=g, hit_vs_up_low=a, hit_vs_up_high=b)
                    g, a, b = bbm(x - pnl["ALWAYS_UP"].to_numpy(float)[msk], int(h), 2000, 590)
                    row.update(pnl_vs_long=g * 252, pnl_vs_long_low=a * 252, pnl_vs_long_high=b * 252)
                if m in models or m == "B0":
                    q = s["p_" + m].to_numpy(float)
                    if m != "B0":
                        row["auc"] = roc_auc_score(y, q)
                        g, a, b = bbm(ll(s.p_B0.to_numpy(float)) - ll(q), int(h), 2000, 590)
                        row.update(logloss_gain_vs_B0=g, ll_low=a, ll_high=b)
                ref = m.split("_")[0] + "_A"
                if m in models and m != ref:
                    g, a, b = bbm(hit[m] - hit[ref], int(h), 2000, 590)
                    row.update(hit_vs_A=g, hit_vs_A_low=a, hit_vs_A_high=b)
                    g, a, b = bbm(x - pnl[ref].to_numpy(float)[msk], int(h), 2000, 590)
                    row.update(pnl_vs_A=g * 252, pnl_vs_A_low=a * 252, pnl_vs_A_high=b * 252)
                rows.append(row)
    return pd.DataFrame(rows)


def main(a):
    pos_study, load_inputs, bbm = _imports(a.repo)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pdir = Path(a.prices)
    frame = load_inputs(pdir / "coffee_c_vendor_close.csv", pdir / "exchange_sessions.csv",
                        pdir / "vendor_price_metadata.json").frame
    base, mfeats, L, r, roll = market_features(frame, a.fx)
    wx, b1, b2 = weather_features(a.weather, a.nodes, a.z, frame.price_date, a.placebo_shift_years)
    base = base.join(wx)
    sets = {"A": mfeats, "B1": mfeats + b1, "B2": mfeats + b1 + b2}
    end_ok = {h: frame.price_usable.shift(-h).fillna(False).astype(bool) for h in HS}   # close at t+h must exist
    fwd = {h: (L.shift(-h) - L).where(end_ok[h]) for h in HS}
    years = [2012] if a.smoke else list(range(2012, 2027))
    D = dict(base=base, dates=frame.price_date, usable=frame.price_usable.to_numpy(bool), sets=sets, fwd=fwd,
             clf=pos_study._clf, seeds=SEEDS[:1] if a.smoke else SEEDS,
             xgb={**XGB, "n_estimators": 20} if a.smoke else XGB)
    if a.smoke:
        res = [run_fold(y, D) for y in years]
    else:
        res = Parallel(n_jobs=a.jobs)(delayed(run_fold)(y, D) for y in years)
    pred = pd.concat(res).sort_values(["h", "price_date"])
    pred.to_csv(out / "LOCAL_ONLY_direction_predictions.csv", index=False)
    models = [f"{fam}_{s}" for fam in ("XGB", "LIN") for s in sets]
    met = evaluate(pred, frame, r, bbm, models)
    if a.smoke:
        print("smoke ok", pred.shape, met.shape, {s: len(f) for s, f in sets.items()},
              "first train rows:", int(pred.n_train.min()),
              "finite:", bool(np.isfinite(pred.filter(like="p_").to_numpy()).all()))
        return
    met.to_csv(out / "direction_metrics.csv", index=False)
    import sklearn, xgboost
    first = base.loc[np.isfinite(base[sets["B2"]].to_numpy(float)).all(axis=1), "price_date"].min()
    json.dump({"plan_sha256": hashlib.sha256(Path(a.plan).read_bytes()).hexdigest(),
               "placebo_shift_years": a.placebo_shift_years, "price_last_date": str(frame.price_date.max().date()),
               "first_complete_row": str(first.date()), "roll_days_zeroed": int(roll.sum()),
               "feature_counts": {s: len(f) for s, f in sets.items()}, "xgb_params": XGB, "seeds": list(SEEDS),
               "cost_per_unit_turnover": COST,
               "versions": {"xgboost": xgboost.__version__, "sklearn": sklearn.__version__,
                            "pandas": pd.__version__, "numpy": np.__version__}},
              open(out / "RECEIPT.json", "w"), indent=1)
    print("done", pred.shape)


if __name__ == "__main__":
    main(ARGS)
