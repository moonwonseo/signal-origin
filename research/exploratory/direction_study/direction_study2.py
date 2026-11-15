"""Direction of Coffee C returns: ENSO and CFTC positioning. See PLAN2_ENSO_CFTC.md.

Reuses direction_study.py (market features, calibrated XGBoost, folds, evaluation). Usage:
  python direction_study2.py --repo <signal-origin checkout> --prices <full_candidate dir> --fx <usd_brl_daily.csv>
      --enso <nino34_monthly.csv> --cot <cftc csv> --plan <PLAN2.md> --out <dir> [--jobs N] [--smoke]
      [--placebo-shift-years K]
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

sys.path.insert(0, str(Path(__file__).resolve().parent))
import direction_study as ds                                   # noqa: E402

ds.HS = (5, 21, 63)


def enso_features(path, price_dates, shift_years=0):
    e = pd.read_csv(path, parse_dates=["month"]).sort_values("month")
    e = e[e.month >= "1990-01-01"].reset_index(drop=True)
    e["enso_lvl"] = e.nino34_anom.astype(float)
    e["enso_d3"] = e.enso_lvl - e.enso_lvl.shift(3)
    if shift_years:
        for c in ("enso_lvl", "enso_d3"):
            e[c] = np.roll(e[c].to_numpy(), shift_years * 12)
    e["avail"] = e.month + pd.DateOffset(months=1) + pd.Timedelta(days=14)     # 15th of the next month
    m = pd.merge_asof(pd.DataFrame({"price_date": price_dates.values}), e[["avail", "enso_lvl", "enso_d3"]],
                      left_on="price_date", right_on="avail", direction="backward",
                      tolerance=pd.Timedelta(days=45))
    assert (m.avail.dropna() <= m.price_date[m.avail.notna()]).all()
    return m[["enso_lvl", "enso_d3"]].set_index(price_dates.index)


def cot_features(pos_study, path, price_dates, shift_years=0):
    cot = pos_study.load_cot(path)
    if shift_years:
        for c in pos_study.POS:
            cot[c] = np.roll(cot[c].to_numpy(), shift_years * 52)
    a = pos_study.align_cot(price_dates, cot)
    return a[list(pos_study.POS)].set_index(price_dates.index)


def main(a):
    pos_study, load_inputs, bbm = ds._imports(a.repo)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pdir = Path(a.prices)
    frame = load_inputs(pdir / "coffee_c_vendor_close.csv", pdir / "exchange_sessions.csv",
                        pdir / "vendor_price_metadata.json").frame
    base, mfeats, L, r, roll = ds.market_features(frame, a.fx)
    base = base.join(enso_features(a.enso, frame.price_date, a.placebo_shift_years))
    base = base.join(cot_features(pos_study, a.cot, frame.price_date, a.placebo_shift_years))
    sets = {"A": mfeats, "E": mfeats + ["enso_lvl", "enso_d3"], "C": mfeats + list(pos_study.POS)}
    end_ok = {h: frame.price_usable.shift(-h).fillna(False).astype(bool) for h in ds.HS}
    fwd = {h: (L.shift(-h) - L).where(end_ok[h]) for h in ds.HS}
    years = [2012] if a.smoke else list(range(2012, 2027))
    D = dict(hs=ds.HS, base=base, dates=frame.price_date, usable=frame.price_usable.to_numpy(bool), sets=sets, fwd=fwd,
             clf=pos_study._clf, seeds=ds.SEEDS[:1] if a.smoke else ds.SEEDS,
             xgb={**ds.XGB, "n_estimators": 20} if a.smoke else ds.XGB)
    if a.smoke:
        res = [ds.run_fold(y, D) for y in years]
    else:
        res = Parallel(n_jobs=a.jobs)(delayed(ds.run_fold)(y, D) for y in years)
    pred = pd.concat(res).sort_values(["h", "price_date"])
    pred.to_csv(out / "LOCAL_ONLY_direction2_predictions.csv", index=False)
    models = [f"{fam}_{s}" for fam in ("XGB", "LIN") for s in sets]
    met = ds.evaluate(pred, frame, r, bbm, models)
    if a.smoke:
        print("smoke ok", pred.shape, met.shape, {s: len(f) for s, f in sets.items()},
              "first train rows:", int(pred.n_train.min()),
              "finite:", bool(np.isfinite(pred.filter(like="p_").to_numpy()).all()))
        return
    met.to_csv(out / "direction2_metrics.csv", index=False)
    first = base.loc[np.isfinite(base[sorted(set(sets["E"] + sets["C"]))].to_numpy(float)).all(axis=1),
                     "price_date"].min()
    json.dump({"plan_sha256": hashlib.sha256(Path(a.plan).read_bytes()).hexdigest(),
               "placebo_shift_years": a.placebo_shift_years, "first_complete_row": str(first.date()),
               "feature_counts": {s: len(f) for s, f in sets.items()}, "horizons": list(ds.HS)},
              open(out / "RECEIPT.json", "w"), indent=1)
    print("done", pred.shape)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    for x in ("repo", "prices", "fx", "enso", "cot", "plan", "out"):
        ap.add_argument("--" + x, required=True)
    ap.add_argument("--jobs", type=int, default=-1)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--placebo-shift-years", type=int, default=0)
    main(ap.parse_args())
