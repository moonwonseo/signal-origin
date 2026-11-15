"""Autoresearch eval and harness (fixed parts of Autoresearch_PLAN.md, sections 1-7 and 9).

Candidates cannot change this file. Run on the Mac mini:
  python core.py base                      score the baselines B0-B5
  python core.py iter candidates/cNN.py    one counted iteration
  python core.py ablate <id>               same candidate without its alt-data features (not an iteration)
  python core.py placebo <id>              17 rotated-data runs (not an iteration)
  python core.py final <id>                the one look at the test period 2023-Oct 2026
"""
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

ROOT = Path(__file__).resolve().parent
PROJ = ROOT.parent
DATA = PROJ / "data"
sys.path.insert(0, str(PROJ / "repo" / "research" / "exploratory" / "cftc_positioning"))
sys.path.insert(0, str(PROJ / "repo"))
sys.path.insert(0, str(ROOT))

LOOP_CUTOFF, FINAL_CUTOFF = "2022-12-31", "2026-12-31"
DEV, TEST = ("2009-01-01", "2022-12-31"), ("2023-01-01", "2026-12-31")
HALVES = (("2009-01-01", "2015-12-31"), ("2016-01-01", "2022-12-31"))
LEAK_T = ("2012-06-29", "2017-06-30", "2021-06-30")
H, COST, SE0, N0, MAX_ITER, MAX_FEATS, MIN_TRAIN = 63, 0.0005, 0.28, 10, 100, 20, 250   # 100: addendum 2
BLOCK, DRAWS, BSEED = 63, 2000, 590
SEEDS = (590, 591, 592, 593, 594)
ROT_START = "1996-01-02"
REV = 1          # 1 = roll repair of 15 Nov 2026 (plan addendum 1): the marked roll day and the next session are zeroed
WX_LAG, MJO_LAG = 4, 5
LOG = ROOT / "trial_log.jsonl"
STATE = ROOT / "state.json"
_cache = {}


def _read(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


def _cards():
    return {p.stem: json.loads(p.read_text()) for p in sorted((ROOT / "data_cards").glob("*.json"))}


class Data:
    """All tables, cut so that nothing published after `cutoff` exists. rot = placebo rotation in years
    (alt data only). Each accessor applies the minimum publication delay of the plan in the cut."""

    def __init__(self, cutoff=LOOP_CUTOFF, rot=0):
        self.cutoff, self.rot = pd.Timestamp(cutoff), int(rot)
        cal = _read("cal", lambda: pd.read_csv(DATA / "prices/exchange_sessions.csv", parse_dates=["session_date"]))
        raw = _read("px", lambda: pd.read_csv(DATA / "prices/coffee_c_vendor_close.csv", parse_dates=["price_date"]))
        f = cal.rename(columns={"session_date": "price_date"}).merge(raw, how="left", on="price_date")
        f = f[f.price_date <= self.cutoff].reset_index(drop=True)
        usable = f.quality_status.eq("ok") & f.close_us_cents_per_lb.notna()
        px = f.close_us_cents_per_lb.astype(float).where(usable).ffill()
        r = np.log(px).diff()
        flag = f.suspected_roll_flag.astype(str).str.lower().eq("true")
        r = r.where(~(flag | flag.shift(1, fill_value=False)), 0.0)   # REV 1: the contract gap is in the next session
        L = r.fillna(0.0).cumsum()
        L[px.isna()] = np.nan
        self.dates, self.usable, self.r, self.L, self.n = f.price_date, usable, r, L, len(f)

    def labels(self):
        g = self.L.rolling(H, min_periods=H).mean().shift(-H) - self.L
        return (g > 0).astype(float).where(g.notna()), g, self.dates.shift(-H)

    # ---- alignment to sessions -------------------------------------------------------------------------
    def align_daily(self, df, lag_days):
        """Value of a calendar-daily table at (session date - lag_days)."""
        out = df.reindex((self.dates - pd.Timedelta(days=int(lag_days))).values)
        out.index = self.dates.index
        return out

    def align_prev(self, s, tol_days=7):
        """Last value dated strictly before the session (market data that closes after Coffee C)."""
        t = pd.DataFrame({"date": pd.to_datetime(s.index), "v": np.asarray(s, float)}).sort_values("date")
        m = pd.merge_asof(pd.DataFrame({"price_date": self.dates.values}), t, left_on="price_date", right_on="date",
                          direction="backward", allow_exact_matches=False, tolerance=pd.Timedelta(days=tol_days))
        return pd.Series(m.v.to_numpy(), index=self.dates.index)

    def align_avail(self, tbl, cols, tol_days):
        """Last row whose 'avail' date is on or before the session."""
        m = pd.merge_asof(pd.DataFrame({"price_date": self.dates.values}), tbl[["avail", *cols]].sort_values("avail"),
                          left_on="price_date", right_on="avail", direction="backward",
                          tolerance=pd.Timedelta(days=tol_days))
        return m[list(cols)].set_index(self.dates.index)

    def _rot_daily(self, df):
        if not self.rot:
            return df
        x = df.loc[ROT_START:]
        return pd.DataFrame(np.roll(x.to_numpy(), self.rot * 365, axis=0), index=x.index, columns=x.columns)

    # ---- market data (never rotated) -------------------------------------------------------------------
    def market_daily(self, name="usd_brl"):
        """Log close by date, rows dated before the cutoff. Use with align_prev."""
        if name == "usd_brl":
            t = _read("fx", lambda: pd.read_csv(DATA / "fx/usd_brl_daily.csv", parse_dates=["date"]))
            t = t.rename(columns={"usd_brl_close": "close"})
        else:
            card = _cards()[name]
            assert card["kind"] == "market_daily"
            t = _read(name, lambda: pd.read_csv(PROJ / card["file"], parse_dates=["date"]))
        t = t[t.date < self.cutoff].sort_values("date")
        return pd.Series(np.log(t.close.astype(float).to_numpy()), index=t.date.to_numpy())

    # ---- alt data (rotated in placebo runs) ------------------------------------------------------------
    def weather_z(self):
        """(rain_z, temp_z): daily node z-scores against earlier years. Use with align_daily(lag >= 4)."""
        out = []
        for nm in ("rain_z", "temp_z"):
            z = _read(nm, lambda nm=nm: pd.read_csv(DATA / "z_long" / f"{nm}.csv", index_col=0, parse_dates=True))
            out.append(self._rot_daily(z[z.index <= self.cutoff - pd.Timedelta(days=WX_LAG)]))
        return out

    def weather_raw(self, col, file="power_daily_arabica_world.csv"):
        """Daily POWER variable by node (calendar index). Use with align_daily(lag >= 4)."""
        def load():
            p = DATA / file if (DATA / file).exists() else ROOT / "data" / file
            d = pd.read_csv(p, parse_dates=["weather_date_utc"])
            return {c: d.pivot(index="weather_date_utc", columns="region_id", values=c)
                    for c in d.columns if c not in ("weather_date_utc", "region_id", "country")}
        t = _read("raw_" + file, load)[col]
        return self._rot_daily(t[t.index <= self.cutoff - pd.Timedelta(days=WX_LAG)])

    def nodes(self):
        return _read("nodes", lambda: pd.read_csv(DATA / "arabica_world_nodes.csv").set_index("region_id"))

    def monthly(self, name="nino34"):
        """Monthly table [month, value, avail]. avail = 15th of month + delay_months (card; minimum 1)."""
        card = _cards()[name]
        assert card["kind"] == "monthly" and int(card["delay_months"]) >= 1
        t = _read(name, lambda: pd.read_csv(PROJ / card["file"], parse_dates=["month"])).sort_values("month")
        t = t[t.month >= card.get("start", "1990-01-01")].reset_index(drop=True)
        t = pd.DataFrame({"month": t.month, "value": t[card["column"]].astype(float)})
        t["avail"] = t.month + pd.DateOffset(months=int(card["delay_months"])) + pd.Timedelta(days=14)
        t = t[t.avail <= self.cutoff].reset_index(drop=True)
        if self.rot and card.get("alt", True):
            t["value"] = np.roll(t.value.to_numpy(), self.rot * 12)
        return t

    def daily_alt(self, name):
        """Calendar-daily alt table from a card (for example MJO). Cut at cutoff - delay_days."""
        card = _cards()[name]
        assert card["kind"] == "daily_alt" and int(card["delay_days"]) >= MJO_LAG
        t = _read(name, lambda: pd.read_csv(PROJ / card["file"], index_col=0, parse_dates=True)).sort_index()
        return self._rot_daily(t[t.index <= self.cutoff - pd.Timedelta(days=int(card["delay_days"]))])

    def cot(self):
        """CFTC managed-money table with 'avail' (report date + 6 days)."""
        import pos_study
        t = _read("cot", lambda: pos_study.load_cot(DATA / "cftc/cftc_coffee_c_disaggregated_72hh-3qpy.csv")).copy()
        t = t.rename(columns={"available_date": "avail"})
        t = t[t.avail <= self.cutoff].reset_index(drop=True)
        if self.rot:
            for c in ("oi", "mm_long", "mm_short", "mm_net_share", "mm_net_change_4w"):
                t[c] = np.roll(t[c].to_numpy(), self.rot * 52)
        return t


# ---- candidates --------------------------------------------------------------------------------------
def load_candidate(path_or_id):
    p = Path(path_or_id)
    if not p.exists():
        p = ROOT / "candidates" / f"{path_or_id}.py"
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    assert getattr(m, "D_BAND", 0.0) in (0.0, 0.05, 0.10) and getattr(m, "SMOOTH", 1) in (1, 5, 21)
    return m


def features(cand, D, drop=()):
    X = cand.features(D)
    assert len(X) == D.n and (X.index == D.dates.index).all()
    assert X.shape[1] <= MAX_FEATS, f"{X.shape[1]} features > {MAX_FEATS}"
    return X.drop(columns=list(drop)) if drop else X


def probabilities(cand, D, years, drop=()):
    """Walk-forward probabilities of y = 1. Expanding window, purged by the 63-session label."""
    if hasattr(cand, "ENSEMBLE"):
        assert len(cand.ENSEMBLE) <= 3
        ps = [probabilities(load_candidate(i), D, years, drop)[0] for i in cand.ENSEMBLE]
        return np.nanmean(np.where(np.isnan(ps).any(axis=0), np.nan, ps), axis=0), {}
    X = features(cand, D, drop)
    y, g, end = D.labels()
    ok = np.isfinite(X.to_numpy(float)).all(axis=1) & D.usable.to_numpy()
    seeds = SEEDS[:int(getattr(cand, "SEEDS", 1))]
    yr = D.dates.dt.year.to_numpy()

    def one(Y):
        iny = yr == Y
        if not iny.any():
            return None
        start = D.dates[iny].min()
        tr = ok & y.notna().to_numpy() & (end < start).to_numpy()
        te = ok & iny
        if tr.sum() < MIN_TRAIN or not te.any():
            return None
        assert end[tr].max() < start
        p = np.mean([cand.fit_predict(X[tr], y[tr].to_numpy(int), g[tr].to_numpy(float), X[te], s)
                     for s in seeds], axis=0)
        return te, np.asarray(p, float), int(tr.sum())

    prob, ntr = np.full(D.n, np.nan), {}
    for Y, res in zip(years, Parallel(n_jobs=min(len(years), 12), prefer="threads")(delayed(one)(Y) for Y in years)):
        if res is not None:
            prob[res[0]] = res[1]
            ntr[Y] = res[2]
    return prob, ntr


def position(prob, D, band=0.0, smooth=1):
    s = pd.Series(prob)
    ps = s.rolling(smooth, min_periods=1).mean() if smooth > 1 else s
    q = np.where(ps > 0.5 + band, 1.0, np.where(ps < 0.5 - band, -1.0, 0.0))
    q[s.isna().to_numpy()] = 0.0
    return weekly(pd.Series(q), D)


def weekly(q, D):
    iso = D.dates.dt.isocalendar()
    key = iso.year.astype(int) * 100 + iso.week.astype(int)
    dec = (key != key.shift(-1)).to_numpy()                 # last session of each calendar week
    return pd.Series(np.where(dec, q, np.nan)).ffill().fillna(0.0)


def saving(p, D, cost=COST):
    p1, p2 = p.shift(1).fillna(0.0), p.shift(2).fillna(0.0)
    return (p1 * D.r.fillna(0.0) - cost * (p1 - p2).abs()).to_numpy(float)


# ---- eval --------------------------------------------------------------------------------------------
def ratio(x):
    sd = x.std(ddof=1) if len(x) > 1 else 0.0
    return float(x.mean() / sd * np.sqrt(252)) if sd > 0 else 0.0


def emax(n):
    from scipy import integrate, stats
    return integrate.quad(lambda x: x * n * stats.norm.pdf(x) * stats.norm.cdf(x) ** (n - 1), -10, 10)[0]


def boot_idx(n):
    rng = np.random.default_rng(BSEED)
    starts = rng.integers(0, n - BLOCK + 1, size=(DRAWS, int(np.ceil(n / BLOCK))))
    return (starts[:, :, None] + np.arange(BLOCK)[None, None, :]).reshape(DRAWS, -1)[:, :n]


def boot_ratio(x, idx):
    xs = x[idx]
    sd = xs.std(axis=1, ddof=1)
    return np.where(sd > 0, xs.mean(axis=1) / np.where(sd > 0, sd, 1.0) * np.sqrt(252), 0.0)


def mask(D, span):
    return D.dates.between(*span).to_numpy()


def metrics(p, prob, D, span, n_trials):
    from sklearn.metrics import roc_auc_score
    m, sv = mask(D, span), saving(p, D)
    x = sv[m]
    yrs = D.dates.dt.year.to_numpy()[m]
    br = boot_ratio(x, boot_idx(len(x)))
    out = dict(ratio=ratio(x), n_days=int(m.sum()), boot_lo=float(np.percentile(br, 2.5)),
               boot_hi=float(np.percentile(br, 97.5)), boot_se=float(br.std(ddof=1)),
               ratio_10bp=ratio(saving(p, D, 0.0010)[m]),
               years_pos=int(sum(x[yrs == y].sum() > 0 for y in np.unique(yrs))), years=int(len(np.unique(yrs))),
               pct_cost_saved=float(x.mean() * 252 * 12.5), turnover_per_year=float(p.diff().abs()[m].sum() / (m.sum() / 252)),
               share_early=float((p[m] > 0).mean()), share_late=float((p[m] < 0).mean()))
    if span == DEV:
        out["ratio_h1"], out["ratio_h2"] = (ratio(sv[mask(D, h)]) for h in HALVES)
        out["score"] = out["ratio"] - SE0 * emax(n_trials)
        out["N"] = n_trials
    r = D.r.fillna(0.0).to_numpy()[m]
    beta = float(np.cov(x, r)[0, 1] / r.var(ddof=1))
    out["beta"], out["alpha_ann"] = beta, float((x.mean() - beta * r.mean()) * 252)
    y, _, _ = D.labels()
    yy, pp = y.to_numpy(), p.to_numpy()
    k = m & ~np.isnan(yy)
    if prob is not None and (k & ~np.isnan(prob)).sum() > 50:
        kk = k & ~np.isnan(prob)
        out["auroc"] = float(roc_auc_score(yy[kk], prob[kk]))
    act = k & (pp != 0)
    out["hit"] = float(((pp[act] > 0) == (yy[act] > 0)).mean()) if act.any() else None
    fmax = D.L[::-1].rolling(H, min_periods=H).max()[::-1].shift(-1) - D.L
    ev = (fmax >= np.log(1.10)).to_numpy() & m & fmax.notna().to_numpy()
    kn = m & fmax.notna().to_numpy()
    out["rise_days_share"] = float(ev.sum() / max(kn.sum(), 1))
    out["recall_rise"] = float((pp[ev] > 0).mean()) if ev.any() else None
    out["precision_rise"] = float(ev[kn & (pp > 0)].mean()) if (kn & (pp > 0)).any() else None
    return out, sv


def leak_test(cand, X):
    """C1: features at dates <= T do not change when everything published after T is removed."""
    if hasattr(cand, "ENSEMBLE"):
        return True, ""
    for T in LEAK_T:
        DT = Data(T)
        a = features(cand, DT).to_numpy(float)
        b = X.iloc[:DT.n].to_numpy(float)
        bad = ~np.isclose(a, b, rtol=0, atol=1e-12, equal_nan=True)
        if bad.any():
            cols = [c for c, f in zip(X.columns, bad.any(axis=0)) if f]
            return False, f"T={T}: {int(bad.sum())} cells differ in {cols[:6]}"
    return True, ""


# ---- log ---------------------------------------------------------------------------------------------
def log_rows(rev=REV):
    rows = [json.loads(x) for x in LOG.read_text().splitlines()] if LOG.exists() else []
    return rows if rev is None else [r for r in rows if r.get("rev", 0) == rev]


def log_append(rec):
    prev = hashlib.sha256(LOG.read_bytes().splitlines()[-1]).hexdigest() if LOG.exists() and LOG.stat().st_size else "0" * 64
    rec = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "rev": REV, **rec, "prev": prev}
    with open(LOG, "a") as f:
        f.write(json.dumps(rec, default=float) + "\n")


def save_run(cid, prob, p, sv, D, tag="dev"):
    o = ROOT / "out" / cid
    o.mkdir(parents=True, exist_ok=True)
    np.save(o / f"saving_{tag}.npy", sv)
    np.save(o / f"prob_{tag}.npy", prob if prob is not None else np.full(D.n, np.nan))
    np.save(o / f"pos_{tag}.npy", p.to_numpy())


def run_candidate(cand, D, years, drop=()):
    prob, ntr = probabilities(cand, D, years, drop)
    p = position(prob, D, getattr(cand, "D_BAND", 0.0), getattr(cand, "SMOOTH", 1))
    return prob, p, ntr


def show(tag, m, extra=""):
    f = lambda v: "  n/a" if v is None else f"{v:6.3f}"
    print(f"{tag:<10} RATIO {m['ratio']:+.3f} [{m['boot_lo']:+.2f},{m['boot_hi']:+.2f}]"
          + (f" SCORE {m['score']:+.3f} (N={m['N']}) halves {m['ratio_h1']:+.2f}/{m['ratio_h2']:+.2f}" if "score" in m else "")
          + f" yrs+ {m['years_pos']}/{m['years']} 10bp {m['ratio_10bp']:+.2f} saved {m['pct_cost_saved']:+.2f}%"
          f" auroc {f(m.get('auroc'))} hit {f(m.get('hit'))} recall {f(m.get('recall_rise'))}"
          f" prec {f(m.get('precision_rise'))} early/late {m['share_early']:.2f}/{m['share_late']:.2f}"
          f" turn {m['turnover_per_year']:.1f} beta {m['beta']:+.2f} {extra}")


# ---- commands ----------------------------------------------------------------------------------------
def cmd_base(plan_sha):
    assert not LOG.exists(), "the log exists already"
    log_append(dict(kind="plan", plan_sha256=plan_sha, core_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    _score_baselines()


def cmd_rescore(reason):
    """After a repair of the eval: score the baselines and all logged iterations again, in order. N does not change."""
    old = [r for r in log_rows(REV - 1) if r["kind"] == "iter"]
    assert not log_rows(REV), "this revision has rows already"
    log_append(dict(kind="repair", reason=reason, core_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    _score_baselines()
    for r in old:
        cmd_iter(f"candidates/{r['id']}.py")


def _score_baselines():
    import lib
    D = Data()
    years = list(range(2009, 2023))
    best = None
    for cid, mk in lib.BASELINES.items():
        obj = mk()
        if callable(getattr(obj, "features", None)):
            ok, why = leak_test(obj, features(obj, D))
            assert ok, why
            prob, p, _ = run_candidate(obj, D, years)
        else:
            prob, p = None, weekly(obj(D), D)
        m, sv = metrics(p, prob, D, DEV, N0)
        save_run(cid, prob, p, sv, D)
        log_append(dict(kind="baseline", id=cid, metrics=m))
        show(cid, m)
        if best is None or m["ratio"] > best[1]:
            best = (cid, m["ratio"])
    STATE.write_text(json.dumps(dict(best=best[0], best_ratio=best[1])))
    print("current best:", best)


def constraints(m, base):
    return dict(C2=m["ratio"] > max(base["B1"], base["B2"], 0.0), C3=m["ratio_h1"] > 0 and m["ratio_h2"] > 0,
                C4=m["years_pos"] >= 8, C5=m["ratio_10bp"] > 0, C7=m["ratio"] < 1.5)


def cmd_iter(path):
    cand = load_candidate(path)
    rows = log_rows()
    done = [r for r in rows if r["kind"] == "iter"]
    assert cand.ID not in {r["id"] for r in done}, "this id has a score already"
    it = len(done) + 1
    assert it <= MAX_ITER, "the budget of iterations is used"
    N = N0 + it
    state = json.loads(STATE.read_text())
    log_append(dict(kind="pre", id=cand.ID, iter=it, parent=cand.PARENT, hypothesis=cand.HYP, change=cand.CHANGE,
                    expect=cand.EXPECT, file_sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest()))
    D = Data()
    X = None if hasattr(cand, "ENSEMBLE") else features(cand, D)
    ok, why = leak_test(cand, X)
    if not ok:
        log_append(dict(kind="iter", id=cand.ID, iter=it, N=N, C1=False, why=why, accepted=False))
        print(f"{cand.ID} iter {it}: C1 LEAK TEST FAILED ({why}). Counted, no score.")
        return
    prob, p, ntr = run_candidate(cand, D, list(range(2009, 2023)))
    m, sv = metrics(p, prob, D, DEV, N)
    base = {r["id"]: r["metrics"]["ratio"] for r in rows if r["kind"] == "baseline"}
    c = constraints(m, base)
    mk = mask(D, DEV)
    best_sv = np.load(ROOT / "out" / state["best"] / "saving_dev.npy")[mk]
    idx = boot_idx(int(mk.sum()))
    diff = boot_ratio(sv[mk], idx) - boot_ratio(best_sv, idx)
    p20 = float(np.percentile(diff, 20))
    accepted = bool(p20 > 0)
    save_run(cand.ID, prob, p, sv, D)
    log_append(dict(kind="iter", id=cand.ID, iter=it, N=N, C1=True, constraints=c, metrics=m,
                    n_features=0 if X is None else int(X.shape[1]), features=[] if X is None else list(X.columns),
                    train_rows_first=min(ntr.values()) if ntr else None, vs_best=state["best"],
                    diff_vs_best=float(m["ratio"] - state["best_ratio"]), diff_p20=p20, accepted=accepted))
    if accepted:
        STATE.write_text(json.dumps(dict(best=cand.ID, best_ratio=m["ratio"])))
    show(f"{cand.ID} it{it}", m)
    print(f"  constraints {c} | vs best {state['best']} ({state['best_ratio']:+.3f}): diff {m['ratio'] - state['best_ratio']:+.3f},"
          f" p20 {p20:+.3f} -> {'ACCEPTED, new best' if accepted else 'rejected'} | need RATIO {SE0 * emax(N):.3f}"
          f" | feats {0 if X is None else X.shape[1]} | first train rows {min(ntr.values()) if ntr else None}")


def cmd_void(cid, reason="see journal"):
    """Addendum 1: a candidate whose feature does not measure what its hypothesis states (shown by a check that
    does not use its score) keeps its row and its count in N, but it cannot be the current best."""
    log_append(dict(kind="void", id=cid, reason=reason))
    rows = log_rows()
    void = {r["id"] for r in rows if r["kind"] == "void"}
    D = Data()
    mk = mask(D, DEV)
    idx = boot_idx(int(mk.sum()))
    sv = lambda i: np.load(ROOT / "out" / i / "saving_dev.npy")[mk]
    base = {r["id"]: r["metrics"]["ratio"] for r in rows if r["kind"] == "baseline"}
    best = max(base, key=base.get)
    for r in [r for r in rows if r["kind"] == "iter" and r.get("C1") and r["id"] not in void]:
        if np.percentile(boot_ratio(sv(r["id"]), idx) - boot_ratio(sv(best), idx), 20) > 0:
            best = r["id"]
    STATE.write_text(json.dumps(dict(best=best, best_ratio=ratio(sv(best)))))
    print("void:", cid, "| current best is now", best, f"{ratio(sv(best)):+.3f}")


def cmd_note(kind, text):
    """A row in the log that is not a score (for example a plan addendum)."""
    log_append(dict(kind=kind, text=text, core_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))
    print("logged", kind)


def cmd_ablate(cid):
    cand = load_candidate(cid)
    D = Data()
    prob, p, _ = run_candidate(cand, D, list(range(2009, 2023)), drop=cand.ALT)
    m, sv = metrics(p, prob, D, DEV, N0)
    full = ratio(np.load(ROOT / "out" / cid / "saving_dev.npy")[mask(D, DEV)])
    log_append(dict(kind="ablate", id=cid, dropped=list(cand.ALT), ratio_without_alt=m["ratio"], ratio_full=full))
    print(f"{cid}: RATIO full {full:+.3f}, without alt data {m['ratio']:+.3f}, gain {full - m['ratio']:+.3f}")


def cmd_placebo(cid):
    cand = load_candidate(cid)
    full = ratio(np.load(ROOT / "out" / cid / "saving_dev.npy")[mask(Data(), DEV)])
    vals = {}
    for k in range(2, 19):
        D = Data(rot=k)
        prob, p, _ = run_candidate(cand, D, list(range(2009, 2023)))
        vals[k] = ratio(saving(p, D)[mask(D, DEV)])
        print(k, f"{vals[k]:+.3f}", flush=True)
    n_ge = int(sum(v >= full for v in vals.values()))
    log_append(dict(kind="placebo", id=cid, ratio_real=full, placebo=vals, n_placebo_ge_real=n_ge, C6=n_ge == 0))
    print(f"{cid}: real {full:+.3f}; placebo mean {np.mean(list(vals.values())):+.3f}, max {max(vals.values()):+.3f};"
          f" {n_ge} of 17 >= real -> C6 {'PASS' if n_ge == 0 else 'FAIL'}")


def cmd_final(cid):
    cand = load_candidate(cid)
    D = Data(FINAL_CUTOFF)
    prob, p, _ = run_candidate(cand, D, list(range(2009, 2027)))
    md, _ = metrics(p, prob, D, DEV, N0 + len([r for r in log_rows() if r["kind"] == "iter"]))
    mt, sv = metrics(p, prob, D, TEST, 0)
    save_run(cid, prob, p, sv, D, "final")
    log_append(dict(kind="final", id=cid, dev_metrics=md, test_metrics=mt, passed=bool(mt["ratio"] > 0.5)))
    show(cid + " dev", md)
    show(cid + " TEST", mt, f"-> {'PASS' if mt['ratio'] > 0.5 else 'FAIL'} (needs RATIO > 0.5)")


if __name__ == "__main__":
    {"base": cmd_base, "rescore": cmd_rescore, "void": cmd_void, "note": cmd_note, "iter": cmd_iter, "ablate": cmd_ablate, "placebo": cmd_placebo, "final": cmd_final}[sys.argv[1]](*sys.argv[2:])
