"""XGBoost on multi-origin Arabica weather: risk gauge and alpha test. See XGB_Multi_Origin_PLAN.md.

Usage:
  python xgb_study.py --repo <signal-origin checkout on v5-weather> --prices <full_candidate dir>
      --weather <power_daily_arabica_world.csv> --nodes <arabica_world_nodes.csv> --z <dir with rain_z.csv,
      temp_z.csv> --plan <PLAN.md> --out <results dir> [--jobs N] [--smoke]

No leakage: prices through t, weather at t-4 calendar days, PCA / scalers / models fit on training rows only,
training outcomes end before the test year.
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
from scipy.stats import spearmanr

ap = argparse.ArgumentParser()
for a in ("repo", "prices", "weather", "nodes", "z", "plan", "out"):
    ap.add_argument("--" + a, required=True)
ap.add_argument("--jobs", type=int, default=-1)
ap.add_argument("--smoke", action="store_true", help="tiny run to test the code; prints no metrics")
ap.add_argument("--placebo-shift-years", type=int, default=0,
                help="EXPLORATORY placebo: rotate all weather features by this many years (breaks the link to prices)")
ARGS = ap.parse_args() if __name__ == "__main__" else None

LAG = 4
SEEDS = (590, 591, 592, 593, 594)
XGB = dict(n_estimators=300, max_depth=3, learning_rate=0.03, subsample=0.8, colsample_bytree=0.5,
           min_child_weight=20, reg_lambda=1.0, tree_method="hist", n_jobs=1)
P = ["lrv5", "lrv21", "lrv63", "sin_doy", "cos_doy", "ret21", "ret63", "ret126"]
CELLS = [(k, h) for h in (21, 63, 126) for k in (5, 10, 15)]
RET_H = (21, 63)
SCOPES = {"all_2012_2026": (2012, 2026), "2012_2018": (2012, 2018), "2019_onward": (2019, 2026)}
TRAIN_START = pd.Timestamp("2008-01-02")


def _imports(repo):
    repo = Path(repo)
    for sub in ("", "research/exploratory/multi_origin_pca", "research/exploratory/cftc_positioning",
                "research/exploratory/weather_volatility"):
        sys.path.insert(0, str(repo / sub))
    import pca_study, pos_study, vol_study                     # noqa: E401
    from signal_origin.io import load_inputs
    from signal_origin.uncertainty import block_bootstrap_mean
    from signal_origin.v5_labels import threshold_labels
    return pca_study, pos_study, vol_study, load_inputs, block_bootstrap_mean, threshold_labels


def weather_features(weather_csv, nodes_csv, zdir, price_dates, shift_years=0):
    """RAW (74 node z-scores) and CTY (country aggregates + Brazil frost), aligned to price dates at t-LAG."""
    rain = pd.read_csv(Path(zdir) / "rain_z.csv", index_col=0, parse_dates=True)
    temp = pd.read_csv(Path(zdir) / "temp_z.csv", index_col=0, parse_dates=True)
    nodes = pd.read_csv(nodes_csv).set_index("region_id")
    assert sorted(rain.columns) == sorted(nodes.index) == sorted(temp.columns)
    raw = pd.concat([rain.add_prefix("rz_"), temp.add_prefix("tz_")], axis=1)
    cty = {}
    for c, ids in nodes.groupby("country").groups.items():
        tag = c.lower()[:3]
        for nm, z in (("rain", rain), ("temp", temp)):
            m = z[list(ids)].mean(axis=1, skipna=False)
            cty[f"c_{nm}30_{tag}"] = m
            cty[f"c_{nm}90_{tag}"] = m.rolling(90, min_periods=90).mean()
    d = pd.read_csv(weather_csv, parse_dates=["weather_date_utc"],
                    usecols=["weather_date_utc", "region_id", "country", "temperature_min_c"])
    bz = d[d.country.eq("Brazil")].pivot(index="weather_date_utc", columns="region_id", values="temperature_min_c")
    bz = bz.min(axis=1, skipna=False)
    cty["bra_tmin_low30"] = bz.rolling(30, min_periods=30).min()
    cty["bra_tmin_low90"] = bz.rolling(90, min_periods=90).min()
    cty = pd.DataFrame(cty).reindex(rain.index)
    if shift_years:                                           # circular shift in whole years keeps the seasons
        def rot(x):                                           # rotate inside the window that has z-scores
            x = x.loc["2007-04-01":]
            return pd.DataFrame(np.roll(x.to_numpy(), shift_years * 365, axis=0), index=x.index, columns=x.columns)
        rain, temp, raw, cty = rot(rain), rot(temp), rot(raw), rot(cty)
    wd = (price_dates - pd.Timedelta(days=LAG)).values
    out = pd.concat([raw.reindex(wd), cty.reindex(wd)], axis=1)
    out.index = price_dates.index
    return out, list(raw.columns), list(cty.columns), rain, temp


def xgb_fit_predict(kind, xtr, ytr, xte, seeds, params):
    from xgboost import XGBClassifier, XGBRegressor
    out, imp = np.zeros(len(xte)), np.zeros(xtr.shape[1])
    if kind == "clf" and len(np.unique(ytr)) < 2:
        return np.full(len(xte), float(np.mean(ytr))), imp
    for s in seeds:
        m = (XGBClassifier if kind == "clf" else XGBRegressor)(**params, random_state=s)
        m.fit(xtr, ytr)
        out += m.predict_proba(xte)[:, 1] if kind == "clf" else m.predict(xte)
        imp += m.feature_importances_
    return out / len(seeds), imp / len(seeds)


def run_fold(y, D):
    pca_study, pos_study, vol_study = D["mods"]
    frame, base, sets = D["frame"], D["base"], D["sets"]
    yd = frame.price_date[frame.price_date.dt.year.eq(y)]
    start, end = yd.min(), yd.max()
    pcs, _ = pca_study.fold_pcs(D["rain"], D["temp"], start - pd.Timedelta(days=1), frame.price_date)
    e = base.join(pcs)
    allf = sorted({f for fs in sets.values() for f in fs})
    ok = np.isfinite(e[allf + ["rv63"]].to_numpy(float)).all(axis=1)
    in_year = e.price_date.between(start, end).to_numpy()
    spike, rets, imps = [], [], []
    for h in (21, 63, 126):
        lab_end = frame.price_date.shift(-h)
        trm = ok & (e.price_date >= TRAIN_START).to_numpy() & (lab_end < start).to_numpy()
        if h in RET_H:
            tgt = D["fwd"][h]
            tr, te = e[trm & tgt.notna().to_numpy()], e[ok & in_year]
            assert lab_end[tr.index].max() < start
            o = te[["price_date"]].copy()
            o["h"], o["fold_year"], o["y"] = h, y, tgt[te.index]
            ytr = tgt[tr.index].to_numpy(float)
            for s, f in sets.items():
                o[f"XGB_{s}"], imp = xgb_fit_predict("reg", tr[f].to_numpy(float), ytr, te[f].to_numpy(float),
                                                     D["seeds"], D["xgb"])
                o[f"LIN_{s}"] = pos_study._reg().fit(tr[f], ytr).predict(te[f])
                imps.append(pd.DataFrame({"target": f"ret_h{h}", "set": s, "fold_year": y, "feature": f, "gain": imp}))
            rets.append(o)
        for k in (5, 10, 15):
            lab = D["labels"][(k, h)]
            q = e.copy()
            q["p_V0"] = vol_study.gauge(q.rv63.to_numpy(float), k, h)
            q["lg"] = pos_study._logit(q.p_V0.to_numpy(float))
            has = lab.notna().to_numpy()
            tr, te = q[trm & has], q[ok & in_year & has]
            if not len(te):
                continue
            assert lab_end[tr.index].max() < start
            ytr = lab[tr.index].astype(int).to_numpy()
            o = te[["price_date", "p_V0"]].copy()
            o["k"], o["h"], o["fold_year"] = k, h, y
            o["y"], o["p_B0"] = lab[te.index].astype(float), ytr.mean()
            for s, f0 in sets.items():
                f = f0 + ["lg"]
                o[f"p_XGB_{s}"], imp = xgb_fit_predict("clf", tr[f].to_numpy(float), ytr, te[f].to_numpy(float),
                                                       D["seeds"], D["xgb"])
                o[f"p_LIN_{s}"] = pos_study._clf().fit(tr[f], ytr).predict_proba(te[f])[:, 1]
                imps.append(pd.DataFrame({"target": f"spike_{k}_{h}", "set": s, "fold_year": y, "feature": f,
                                          "gain": imp}))
            spike.append(o)
    return pd.concat(spike), pd.concat(rets), pd.concat(imps)


def boot_spearman(a, b, block, n_boot=2000, seed=590):
    n = len(a)
    block = min(block, n)
    rng = np.random.default_rng(seed)
    starts, kk = np.arange(n - block + 1), int(np.ceil(n / block))
    vals = np.empty(n_boot)
    for i in range(n_boot):
        idx = (rng.choice(starts, kk)[:, None] + np.arange(block)).ravel()[:n]
        vals[i] = spearmanr(a[idx], b[idx]).statistic
    lo, hi = np.nanpercentile(vals, [2.5, 97.5])
    return float(spearmanr(a, b).statistic), float(lo), float(hi)


def main(a):
    mods = _imports(a.repo)
    pca_study, pos_study, vol_study, load_inputs, bbm, threshold_labels = mods
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pdir = Path(a.prices)
    frame = load_inputs(pdir / "coffee_c_vendor_close.csv", pdir / "exchange_sessions.csv",
                        pdir / "vendor_price_metadata.json").frame
    base, r = pos_study.base_frame(frame)
    roll = frame.suspected_roll_flag.astype(str).str.lower().eq("true")
    if os.environ.get("ROLL_FIX") == "1":          # repair of 15 Nov 2026: the contract gap is in the NEXT session
        roll = roll | roll.shift(1, fill_value=False)
    r_adj = r.where(~roll, 0.0)                               # roll jumps are not tradable returns
    for n in (21, 63, 126):
        base[f"ret{n}"] = r_adj.rolling(n, min_periods=n).sum()
    wx, rawf, ctyf, rain, temp = weather_features(a.weather, a.nodes, a.z, frame.price_date,
                                                  a.placebo_shift_years)
    base = base.join(wx)
    sets = {"P": P, "PC": P + list(pca_study.PCS), "RAW": P + rawf, "CTY": P + ctyf}
    fwd = {h: r_adj[::-1].rolling(h, min_periods=h).sum()[::-1].shift(-1) for h in RET_H}
    labels = {(k, h): threshold_labels(frame, h, k)["target_spike"] for k, h in CELLS}
    years = [2012] if a.smoke else list(range(2012, 2027))
    D = dict(mods=(pca_study, pos_study, vol_study), frame=frame, base=base, sets=sets, rain=rain, temp=temp,
             fwd=fwd, labels=labels, seeds=SEEDS[:1] if a.smoke else SEEDS,
             xgb={**XGB, "n_estimators": 20} if a.smoke else XGB)
    if a.smoke:
        res = [run_fold(y, D) for y in years]
    else:
        res = Parallel(n_jobs=a.jobs)(delayed(run_fold)(y, D) for y in years)
    spike = pd.concat([x[0] for x in res]).sort_values(["k", "h", "price_date"])
    rets = pd.concat([x[1] for x in res]).sort_values(["h", "price_date"])
    imps = pd.concat([x[2] for x in res])
    spike.to_csv(out / "LOCAL_ONLY_spike_predictions.csv", index=False)
    rets.to_csv(out / "LOCAL_ONLY_return_predictions.csv", index=False)
    if a.smoke:
        print("smoke ok", spike.shape, rets.shape, imps.shape, {s: len(f) for s, f in sets.items()},
              "finite preds:", bool(np.isfinite(spike.filter(like="p_").to_numpy()).all()))
        return
    models = [f"{fam}_{s}" for fam in ("XGB", "LIN") for s in sets]

    # ---- (a) spike: Brier and paired gains
    rows = []
    for (k, h), p in spike.groupby(["k", "h"]):
        for scope, (lo, hi) in SCOPES.items():
            s = p[p.fold_year.between(lo, hi)]
            loss = {m: ((s["p_" + m] - s.y) ** 2).to_numpy(float) for m in ["B0", "V0", *models]}
            for m in ["B0", "V0", *models]:
                row = dict(k=k, h=h, scope=scope, model=m, n=len(s), event_rate=s.y.mean(), brier=loss[m].mean())
                refs = ["V0", "B0"] + ([m.split("_")[0] + "_P"] if m in models and not m.endswith("_P") else [])
                for ref in refs:
                    if ref != m:
                        g, lo_, hi_ = bbm(loss[ref] - loss[m], int(h), 2000, 590)
                        tag = "P" if ref.endswith("_P") else ref
                        row.update({f"gain_vs_{tag}": g, f"low_vs_{tag}": lo_, f"high_vs_{tag}": hi_})
                rows.append(row)
    pd.DataFrame(rows).to_csv(out / "spike_brier.csv", index=False)

    # ---- (b) alpha: forecast accuracy, rank IC and the trading rule
    dates = frame.price_date
    nxt = r_adj.shift(-1)                                      # return earned from t to t+1
    arow = []
    for h, p in rets.groupby("h"):
        p = p.set_index(p.index)                               # frame index
        pnl = {}
        for m in models:
            sig = pd.Series(np.nan, index=frame.index)
            sig[p.index] = np.sign(p[m].to_numpy(float))
            pos = sig.rolling(h, min_periods=1).mean().fillna(0.0)
            pnl[m] = pd.DataFrame({"pnl": pos * nxt, "turn": pos.diff().abs(), "pos": pos})
        live = pd.Series(False, index=frame.index)
        live[p.index] = True
        live &= nxt.notna()
        pnl["LONG"] = pd.DataFrame({"pnl": nxt, "turn": 0.0, "pos": 1.0})
        for scope, (lo, hi) in SCOPES.items():
            msk = (live & dates.dt.year.between(lo, hi)).to_numpy()
            s = p[p.fold_year.between(lo, hi) & p.y.notna()]
            yv = s.y.to_numpy(float)
            for m in [*models, "LONG"]:
                x = pnl[m].pnl.to_numpy(float)[msk]
                g, lo_, hi_ = bbm(x, int(h), 2000, 590)
                row = dict(h=h, scope=scope, model=m, n_days=int(msk.sum()), pnl_ann=g * 252, pnl_ann_low=lo_ * 252,
                           pnl_ann_high=hi_ * 252, sharpe=x.mean() / x.std(ddof=1) * np.sqrt(252),
                           mean_pos=pnl[m].pos.to_numpy()[msk].mean(),
                           turnover_per_day=pnl[m].turn.to_numpy()[msk].mean())
                if m != "LONG":
                    pv = s[m].to_numpy(float)
                    g, lo_, hi_ = bbm(yv ** 2 - (pv - yv) ** 2, int(h), 2000, 590)
                    row.update(n_fc=len(s), mse_gain_vs_zero=g, mse_low_vs_zero=lo_, mse_high_vs_zero=hi_)
                    ic, lo_, hi_ = boot_spearman(pv, yv, int(h))
                    row.update(rank_ic=ic, ic_low=lo_, ic_high=hi_)
                    g, lo_, hi_ = bbm(x - pnl["LONG"].pnl.to_numpy(float)[msk], int(h), 2000, 590)
                    row.update(pnl_ann_vs_long=g * 252, vs_long_low=lo_ * 252, vs_long_high=hi_ * 252)
                    ref = m.split("_")[0] + "_P"
                    if m != ref:
                        g, lo_, hi_ = bbm(x - pnl[ref].pnl.to_numpy(float)[msk], int(h), 2000, 590)
                        row.update(pnl_ann_vs_P=g * 252, vs_P_low=lo_ * 252, vs_P_high=hi_ * 252)
                        g, lo_, hi_ = bbm((s[ref].to_numpy(float) - yv) ** 2 - (pv - yv) ** 2, int(h), 2000, 590)
                        row.update(mse_gain_vs_P=g, mse_low_vs_P=lo_, mse_high_vs_P=hi_)
                arow.append(row)
    pd.DataFrame(arow).to_csv(out / "alpha.csv", index=False)
    (imps.groupby(["target", "set", "feature"]).gain.mean().reset_index()
         .sort_values(["target", "set", "gain"], ascending=[True, True, False])
         .to_csv(out / "xgb_importance.csv", index=False))
    import sklearn, xgboost
    json.dump({"plan_sha256": hashlib.sha256(Path(a.plan).read_bytes()).hexdigest(),
               "price_last_date": str(dates.max().date()), "n_sessions": int(len(frame)),
               "roll_days_zeroed": int(roll.sum()),
               "placebo_shift_years": a.placebo_shift_years, "feature_counts": {s: len(f) for s, f in sets.items()},
               "xgb_params": XGB, "seeds": list(SEEDS),
               "versions": {"xgboost": xgboost.__version__, "sklearn": sklearn.__version__,
                            "pandas": pd.__version__, "numpy": np.__version__}},
              open(out / "RECEIPT.json", "w"), indent=1)
    print("done", spike.shape, rets.shape)


if __name__ == "__main__":
    main(ARGS)
