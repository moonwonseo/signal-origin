"""Multi-origin weather PCA study (see PLAN.md). PCA refit on pre-test weather only, inside each annual fold."""
import hashlib, json, sys
from pathlib import Path
import numpy as np, pandas as pd
from sklearn.decomposition import PCA

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cftc_positioning"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "weather_volatility"))
from pos_study import _clf, _reg, _logit, base_frame, SCOPES          # noqa: E402
from vol_study import future_rv, gauge                                 # noqa: E402
from signal_origin.io import load_inputs                               # noqa: E402
from signal_origin.uncertainty import block_bootstrap_mean             # noqa: E402
from signal_origin.v5_labels import threshold_labels                   # noqa: E402

HERE = Path(__file__).resolve().parent
K, LAG = 3, 4
PCS = [f"{v}_pc{i}" for v in ("rain", "temp") for i in range(1, K + 1)]
PRICE = ["lrv5", "lrv21", "lrv63", "sin_doy", "cos_doy"]
CELLS = ((5, 21), (5, 63), (5, 126), (10, 21), (10, 63), (10, 126), (15, 21), (15, 63), (15, 126))


def fold_pcs(rain, temp, fit_end, price_dates):
    """Fit PCA on weather dated 2008-01-01 .. fit_end (complete rows only); return PCs at t-LAG for price_dates."""
    out = pd.DataFrame(index=price_dates.index)
    wdates = price_dates - pd.Timedelta(days=LAG)
    info = {}
    for name, z in (("rain", rain), ("temp", temp)):
        fit = z.loc["2008-01-01":fit_end].dropna()
        mu, sd = fit.mean(), fit.std(ddof=0)
        p = PCA(n_components=K, random_state=0).fit((fit - mu) / sd)
        x = z.reindex(wdates.values)
        ok = x.notna().all(axis=1).values
        sc = np.full((len(x), K), np.nan)
        sc[ok] = p.transform(((x - mu) / sd).values[ok])
        for i in range(K):
            out[f"{name}_pc{i+1}"] = sc[:, i]
        info[name] = {"explained": p.explained_variance_ratio_.round(3).tolist(),
                      "loadings": pd.DataFrame(p.components_.T, index=z.columns).round(3).to_dict()}
    return out, info


def main(prices_dir, zdir, out):
    out = Path(out); out.mkdir(exist_ok=True)
    pdir = Path(prices_dir)
    frame = load_inputs(pdir / "coffee_c_vendor_close.csv", pdir / "exchange_sessions.csv",
                        pdir / "vendor_price_metadata.json").frame
    rain = pd.read_csv(Path(zdir) / "rain_z.csv", index_col=0, parse_dates=True)
    temp = pd.read_csv(Path(zdir) / "temp_z.csv", index_col=0, parse_dates=True)
    base, r = base_frame(frame)
    years = range(2012, 2027)
    pcs_by_year, infos = {}, {}
    for y in years:
        start = frame.price_date[frame.price_date.dt.year.eq(y)].min()
        pcs_by_year[y], infos[y] = fold_pcs(rain, temp, start - pd.Timedelta(days=1), frame.price_date)
    spike_rows, vol_rows = [], []
    for h in sorted({h for _, h in CELLS}):
        d = base.copy()
        d["target_lrv"] = np.log(future_rv(r, h).clip(lower=1e-6))
        d["label_end_date"] = frame.price_date.shift(-h)
        labs = {k: threshold_labels(frame, h, k) for k, hh in CELLS if hh == h}
        vp, sp = [], {k: [] for k in labs}
        for y in years:
            e = d.join(pcs_by_year[y])
            ok = np.isfinite(e[PRICE + PCS + ["rv63", "target_lrv"]].to_numpy(float)).all(axis=1)
            yd = e.price_date[e.price_date.dt.year.eq(y)]
            start, end = yd.min(), yd.max()
            trm = ok & (e.price_date >= pd.Timestamp("2008-01-02")) & (e.label_end_date < start)
            tem = ok & e.price_date.between(start, end)
            tr, te = e[trm], e[tem].copy()
            te["fold_year"] = y
            for nm, f in (("V1", PRICE), ("PC1", PRICE + PCS)):
                te["pred_" + nm] = _reg().fit(tr[f], tr.target_lrv).predict(te[f])
            vp.append(te)
            for k, lab in labs.items():
                q = e.join(lab[["target_spike"]])
                q["p_V0"] = gauge(q.rv63.to_numpy(), k, h); q["lg"] = _logit(q.p_V0.to_numpy())
                tr2 = q[trm & q.target_spike.notna()]; te2 = q[tem & q.target_spike.notna()].copy()
                ytr = tr2.target_spike.astype(int)
                te2["fold_year"] = y; te2["p_B0"] = ytr.mean()
                for nm, f in (("G", ["lg"]), ("GPC", ["lg", *PCS])):
                    te2["p_" + nm] = _clf().fit(tr2[f], ytr).predict_proba(te2[f])[:, 1]
                sp[k].append(te2)
        vp = pd.concat(vp)
        for scope, (lo, hi) in SCOPES.items():
            s = vp[vp.fold_year.between(lo, hi)]
            diff = ((s.pred_V1 - s.target_lrv) ** 2 - (s.pred_PC1 - s.target_lrv) ** 2).to_numpy()
            g, a, b = block_bootstrap_mean(diff, int(h), 2000, 590)
            vol_rows.append(dict(h=h, scope=scope, n=len(s), gain_PC1_vs_V1=g, low=a, high=b))
        for k, parts in sp.items():
            p = pd.concat(parts); p["y"] = p.target_spike.astype(float)
            for scope, (lo, hi) in SCOPES.items():
                s = p[p.fold_year.between(lo, hi)]
                for m in ("B0", "V0", "G", "GPC"):
                    row = dict(k=k, h=h, scope=scope, model=m, n=len(s), event_rate=s.y.mean(),
                               brier=((s["p_" + m] - s.y) ** 2).mean())
                    for ref in ("G", "V0", "B0"):
                        if ref != m:
                            diff = ((s["p_" + ref] - s.y) ** 2 - (s["p_" + m] - s.y) ** 2).to_numpy()
                            g, a, b = block_bootstrap_mean(diff, int(h), 2000, 590)
                            row.update({f"gain_vs_{ref}": g, f"low_vs_{ref}": a, f"high_vs_{ref}": b})
                    spike_rows.append(row)
    pd.DataFrame(spike_rows).to_csv(out / "spike_brier.csv", index=False)
    pd.DataFrame(vol_rows).to_csv(out / "volatility.csv", index=False)
    json.dump(infos, open(out / "pca_info.json", "w"), indent=1, default=str)
    json.dump({"plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest()},
              open(out / "RECEIPT.json", "w"))


if __name__ == "__main__":
    main(*sys.argv[1:4])
