"""Do CFTC positioning (and ICE certified stocks) sharpen the price-risk gauge? See PLAN.md.

Local exploratory study. Reads the signal_origin package and local files; writes only to --out.
Timing: CFTC report (Tuesday positions) usable from report date + 6 days (following Monday).
Stocks: usable from the next session. Prices through t only for every feature.
"""
import hashlib
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "weather_volatility"))
from vol_study import future_rv, gauge, log_returns, trailing_rv  # noqa: E402  (tested in the weather study)
from signal_origin.uncertainty import block_bootstrap_mean       # noqa: E402
from signal_origin.v5_labels import threshold_labels              # noqa: E402

HERE = Path(__file__).resolve().parent
COT_LAG_DAYS, COT_MAX_AGE_DAYS = 6, 14
POS = ("mm_net_share", "mm_net_change_4w")
STK = ("stocks_logchg_63",)
SCOPES = {"all_2012_2026": (2012, 2026), "2012_2018": (2012, 2018), "2019_onward": (2019, 2026)}


def _norm(c):
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]", "_", str(c).strip().lower())).strip("_")


def _find(cols, *needles):
    if len(needles) == 1 and needles[0] in cols:
        return needles[0]                      # exact column name wins over longer variants
    hits = [c for c in cols if all(n in c for n in needles)]
    if len(hits) != 1:
        raise ValueError(f"expected one column containing {needles}, found {hits}")
    return hits[0]


def load_cot(path) -> pd.DataFrame:
    """Accepts the CFTC API CSV or the CFTC yearly text files (any header style)."""
    raw = pd.read_csv(path, low_memory=False)
    raw.columns = [_norm(c) for c in raw.columns]
    cols = list(raw.columns)
    name = _find(cols, "market_and_exchange_names")
    date = next(c for c in cols if "report_date" in c and "yyyy" in c and "mm" in c and "dd" in c)
    oi = _find(cols, "open_interest_all")
    lg = [c for c in cols if c.startswith("m_money_positions_long") and c.endswith("_all")][0]
    sh = [c for c in cols if c.startswith("m_money_positions_short") and c.endswith("_all")][0]
    d = raw[raw[name].astype(str).str.upper().str.contains("COFFEE C")].copy()
    if d.empty:
        raise ValueError("no Coffee C rows found")
    d = pd.DataFrame({"report_date": pd.to_datetime(d[date].astype(str).str[:10]),
                      "oi": pd.to_numeric(d[oi]), "mm_long": pd.to_numeric(d[lg]),
                      "mm_short": pd.to_numeric(d[sh])})
    d = d.drop_duplicates("report_date").sort_values("report_date").reset_index(drop=True)
    d["mm_net_share"] = (d.mm_long - d.mm_short) / d.oi
    d["mm_net_change_4w"] = d.mm_net_share - d.mm_net_share.shift(4)
    d["available_date"] = d.report_date + pd.Timedelta(days=COT_LAG_DAYS)
    return d


def align_cot(price_dates: pd.Series, cot: pd.DataFrame) -> pd.DataFrame:
    left = pd.DataFrame({"price_date": price_dates.values})
    m = pd.merge_asof(left, cot[["available_date", "report_date", *POS]].sort_values("available_date"),
                      left_on="price_date", right_on="available_date", direction="backward",
                      tolerance=pd.Timedelta(days=COT_MAX_AGE_DAYS))
    assert (m.available_date.dropna() <= m.price_date[m.available_date.notna()]).all()
    return m


def load_stocks(path) -> pd.DataFrame:
    s = pd.read_csv(path)
    s.columns = [_norm(c) for c in s.columns]
    dcol = next(c for c in s.columns if "date" in c)
    vcol = next(c for c in s.columns if c != dcol and pd.to_numeric(s[c], errors="coerce").notna().mean() > .9)
    s = pd.DataFrame({"stock_date": pd.to_datetime(s[dcol]),
                      "stocks": pd.to_numeric(s[vcol], errors="coerce")}).dropna()
    s = s.drop_duplicates("stock_date").sort_values("stock_date").reset_index(drop=True)
    s["stocks_logchg_63"] = np.log(s.stocks.clip(lower=1)).diff(63)
    return s


def align_stocks(price_dates: pd.Series, stocks: pd.DataFrame) -> pd.DataFrame:
    left = pd.DataFrame({"price_date": price_dates.values})
    return pd.merge_asof(left, stocks[["stock_date", *STK]], left_on="price_date", right_on="stock_date",
                         direction="backward", allow_exact_matches=False,   # next-session availability
                         tolerance=pd.Timedelta(days=7))


def base_frame(frame, cot=None, stocks=None):
    r = log_returns(frame)
    d = frame[["price_date"]].copy()
    for n in (5, 21, 63):
        d[f"lrv{n}"] = np.log(trailing_rv(r, n).clip(lower=1e-6))
    d["rv63"] = trailing_rv(r, 63)
    phase = (d.price_date.dt.dayofyear - 1) / np.where(d.price_date.dt.is_leap_year, 366.0, 365.0)
    d["sin_doy"], d["cos_doy"] = np.sin(2 * np.pi * phase), np.cos(2 * np.pi * phase)
    if cot is not None:
        a = align_cot(d.price_date, cot)
        for c in POS:
            d[c] = a[c].to_numpy()
        d["cot_report_used"] = a.report_date.to_numpy()
    if stocks is not None:
        a = align_stocks(d.price_date, stocks)
        d[STK[0]] = a[STK[0]].to_numpy()
    return d, r


def _logit(p):
    p = np.clip(p, 1e-4, 1 - 1e-4)
    return np.log(p / (1 - p))


def _clf():
    return Pipeline([("scale", StandardScaler()),
                     ("logit", LogisticRegression(C=1.0, solver="lbfgs", max_iter=2000, tol=1e-8))])


def _reg():
    return Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0))])


def run_source(frame, base, r, extra, tag, years=range(2012, 2027), train_start="2008-01-02",
               cells=((5, 21), (5, 63), (5, 126), (10, 21), (10, 63), (10, 126), (15, 21), (15, 63), (15, 126))):
    """extra: feature names of the source being tested (positioning or stocks)."""
    spike_rows, vol_rows, coefs, skipped = [], [], {}, []
    hs = sorted({h for _, h in cells})
    for h in hs:
        d = base.copy()
        d["target_lrv"] = np.log(future_rv(r, h).clip(lower=1e-6))
        d["label_end_date"] = frame.price_date.shift(-h)
        price_feats = ["lrv5", "lrv21", "lrv63", "sin_doy", "cos_doy"]
        need = price_feats + list(extra) + ["rv63", "target_lrv"]
        ok = np.isfinite(d[need].to_numpy(float)).all(axis=1)
        vol_preds = []
        for y in years:
            yd = d.price_date[d.price_date.dt.year.eq(y)]
            start, end = yd.min(), yd.max()
            tr = d[ok & (d.price_date >= pd.Timestamp(train_start)) & (d.label_end_date < start)]
            te = d[ok & d.price_date.between(start, end)].copy()
            if len(tr) < 252 or te.empty:
                skipped.append({"h": h, "year": y, "train_rows": len(tr), "test_rows": len(te)})
                continue
            te["fold_year"] = y
            for name, feats in (("V1", price_feats), (tag + "_vol", price_feats + list(extra))):
                m = _reg().fit(tr[feats], tr.target_lrv)
                te["pred_" + name] = m.predict(te[feats])
                coefs[f"vol/{name}/h{h}/{y}"] = dict(zip(feats, m.named_steps["ridge"].coef_.round(4)))
            vol_preds.append(te)
        vp = pd.concat(vol_preds)
        for scope, (lo, hi) in SCOPES.items():
            s = vp[vp.fold_year.between(lo, hi)]
            if s.empty:
                continue
            la = (s.pred_V1 - s.target_lrv) ** 2
            lb = (s[f"pred_{tag}_vol"] - s.target_lrv) ** 2
            g, a, b = block_bootstrap_mean((la - lb).to_numpy(), int(h), 2000, 590)
            vol_rows.append(dict(h=h, scope=scope, n=len(s), model=f"{tag}_vol", reference="V1", gain=g, low=a, high=b))
        for k, hh in cells:
            if hh != h:
                continue
            lab = threshold_labels(frame, h, k)
            e = d.join(lab[["target_spike"]])
            e["p_V0"] = gauge(e.rv63.to_numpy(), k, h)
            e["lg"] = _logit(e.p_V0.to_numpy())
            ok2 = ok & e.target_spike.notna()
            preds = []
            for y in years:
                yd = e.price_date[e.price_date.dt.year.eq(y)]
                start, end = yd.min(), yd.max()
                tr = e[ok2 & (e.price_date >= pd.Timestamp(train_start)) & (e.label_end_date < start)]
                te = e[ok2 & e.price_date.between(start, end)].copy()
                if len(tr) < 252 or te.empty or tr.target_spike.nunique() < 2:
                    continue
                ytr = tr.target_spike.astype(int)
                te["fold_year"] = y
                te["p_B0"] = ytr.mean()
                for name, feats in (("G", ["lg"]), (tag, ["lg", *extra])):
                    m = _clf().fit(tr[feats], ytr)
                    te["p_" + name] = m.predict_proba(te[feats])[:, 1]
                    coefs[f"spike/{name}/k{k}/h{h}/{y}"] = dict(zip(feats, m.named_steps["logit"].coef_[0].round(4)))
                preds.append(te)
            p = pd.concat(preds)
            p["y"] = p.target_spike.astype(float)
            for scope, (lo, hi) in SCOPES.items():
                s = p[p.fold_year.between(lo, hi)]
                if s.empty:
                    continue
                for mdl in ("B0", "V0", "G", tag):
                    row = dict(k=k, h=h, scope=scope, model=mdl, n=len(s), event_rate=s.y.mean(),
                               mean_prob=s["p_" + mdl].mean(), brier=((s["p_" + mdl] - s.y) ** 2).mean())
                    for ref in ("G", "V0", "B0"):
                        if ref != mdl:
                            diff = ((s["p_" + ref] - s.y) ** 2 - (s["p_" + mdl] - s.y) ** 2).to_numpy()
                            g, a, b = block_bootstrap_mean(diff, int(h), 2000, 590)
                            row.update({f"gain_vs_{ref}": g, f"low_vs_{ref}": a, f"high_vs_{ref}": b})
                    spike_rows.append(row)
    return pd.DataFrame(spike_rows), pd.DataFrame(vol_rows), coefs, skipped


def main(prices_dir, out, cot_path=None, stocks_path=None):
    from signal_origin.io import load_inputs
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    pdir = Path(prices_dir)
    frame = load_inputs(pdir / "coffee_c_vendor_close.csv", pdir / "exchange_sessions.csv",
                        pdir / "vendor_price_metadata.json").frame
    receipt = {"plan_sha256": hashlib.sha256((HERE / "PLAN.md").read_bytes()).hexdigest(), "sources": {}}
    for tag, path, loader, feats in (("GP", cot_path, load_cot, POS), ("GS", stocks_path, load_stocks, STK)):
        if not path:
            continue
        src = loader(path)
        base, r = base_frame(frame, cot=src if tag == "GP" else None, stocks=src if tag == "GS" else None)
        spikes, vol, coefs, skipped = run_source(frame, base, r, feats, tag)
        spikes.to_csv(out / f"{tag}_spike_brier.csv", index=False)
        vol.to_csv(out / f"{tag}_volatility.csv", index=False)
        json.dump(coefs, open(out / f"{tag}_coefficients.json", "w"), indent=1, default=float)
        first = src.iloc[:, 0]
        receipt["sources"][tag] = {"file_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
                                   "rows": len(src), "first": str(first.min().date()), "last": str(first.max().date()),
                                   "skipped_folds": skipped}
    json.dump(receipt, open(out / "RECEIPT.json", "w"), indent=1)


if __name__ == "__main__":
    a = sys.argv[1:]
    main(a[0], a[1], *(x if x not in ("", "-") else None for x in a[2:4]))
