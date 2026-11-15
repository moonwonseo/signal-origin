"""Feature and model helpers for candidates. Candidates import this file; the eval is in core.py."""
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BRAZIL_W = {"sul_de_minas": 0.3561, "matas_de_minas": 0.2102, "cerrado_mineiro": 0.1739, "mogiana_sp": 0.1391,
            "montanhas_es": 0.0975, "planalto_ba": 0.0231}
MARKET13 = ["kret5", "kret21", "kret63", "kret126", "kret252", "lrv21", "lrv63", "sin_doy", "cos_doy",
            "brl_ret5", "brl_ret21", "brl_ret63", "brl_lrv21"]


def price_feats(D):
    d = pd.DataFrame(index=D.dates.index)
    for n in (5, 21, 63, 126, 252):
        d[f"kret{n}"] = D.L - D.L.shift(n)
    for n in (21, 63):
        d[f"lrv{n}"] = np.log(D.r.rolling(n, min_periods=n).std(ddof=1).clip(lower=1e-6))
    phase = (D.dates.dt.dayofyear - 1) / np.where(D.dates.dt.is_leap_year, 366.0, 365.0)
    d["sin_doy"], d["cos_doy"] = np.sin(2 * np.pi * phase), np.cos(2 * np.pi * phase)
    return d


def brl_feats(D):
    d = pd.DataFrame(index=D.dates.index)
    lfx = D.align_prev(D.market_daily("usd_brl"))
    for n in (5, 21, 63):
        d[f"brl_ret{n}"] = lfx - lfx.shift(n)
    d["brl_lrv21"] = np.log(lfx.diff().rolling(21, min_periods=21).std(ddof=1).clip(lower=1e-6))
    return d


def market13(D):
    """The 13 market features of the Direction study (set A)."""
    return price_feats(D).join(brl_feats(D))[MARKET13]


def monthly_feats(D, name, prefix, d=(3,), tol_days=45):
    """Level and k-month changes of a monthly index, aligned by its publication date."""
    t = D.monthly(name)
    cols = [f"{prefix}_lvl"]
    t[cols[0]] = t.value
    for k in d:
        t[f"{prefix}_d{k}"] = t.value - t.value.shift(k)
        cols.append(f"{prefix}_d{k}")
    return D.align_avail(t, cols, tol_days)


def enso2(D):
    return monthly_feats(D, "nino34", "enso")


def cot2(D):
    return D.align_avail(D.cot(), ["mm_net_share", "mm_net_change_4w"], 14)


def country_z(D):
    """Daily country means of the node z-scores (Brazil weighted by output). Calendar index."""
    rain, temp = D.weather_z()
    nodes, w, out = D.nodes(), pd.Series(BRAZIL_W) / sum(BRAZIL_W.values()), {}
    for c, ids in nodes.groupby("country").groups.items():
        tag = c.lower()[:3]
        for nm, z in (("rain", rain), ("temp", temp)):
            out[f"{nm}_{tag}"] = (z[list(w.index)] * w).sum(axis=1, skipna=False) if c == "Brazil" \
                else z[list(ids)].mean(axis=1, skipna=False)
    return pd.DataFrame(out)


def logit_fp(C=1.0):
    def fp(Xtr, ytr, gtr, Xte, seed):
        m = Pipeline([("scale", StandardScaler()),
                      ("logit", LogisticRegression(C=C, solver="lbfgs", max_iter=2000, tol=1e-8))])
        return m.fit(Xtr, ytr).predict_proba(Xte)[:, 1]
    return fp


def sk_fp(make):
    """make(seed) -> sklearn-style classifier."""
    def fp(Xtr, ytr, gtr, Xte, seed):
        return make(seed).fit(Xtr.to_numpy(float), ytr).predict_proba(Xte.to_numpy(float))[:, 1]
    return fp


def _const(v):
    return lambda D: pd.Series(float(v), index=D.dates.index)


BASELINES = {
    "B0": lambda: _const(0), "B1": lambda: _const(1), "B2": lambda: _const(-1),
    "B3": lambda: (lambda D: np.sign(D.L - D.L.shift(63)).fillna(0.0)),
    "B4": lambda: SimpleNamespace(features=market13, fit_predict=logit_fp(1.0)),
    "B5": lambda: SimpleNamespace(features=lambda D: market13(D).join(enso2(D)), fit_predict=logit_fp(1.0)),
}


# ---- helpers added during the loop (candidate side; the eval in core.py does not change) ---------------
_PX = None


def rule_fp(col, sign=1.0, thr=0.0):
    """Unfitted rule on one feature: probability 1 if sign * (x - thr) > 0, else 0."""
    def fp(Xtr, ytr, gtr, Xte, seed):
        return (sign * (Xte[col].to_numpy(float) - thr) > 0).astype(float)
    return fp


def raw_px(D):
    """Raw vendor close, roll flag and volume on the session calendar, cut at D.cutoff."""
    global _PX
    if _PX is None:
        base = Path(__file__).resolve().parent.parent / "data" / "prices"
        _PX = (pd.read_csv(base / "exchange_sessions.csv", parse_dates=["session_date"]),
               pd.read_csv(base / "coffee_c_vendor_close.csv", parse_dates=["price_date"]))
    cal, raw = _PX
    f = cal.rename(columns={"session_date": "price_date"}).merge(raw, how="left", on="price_date")
    f = f[f.price_date <= D.cutoff].reset_index(drop=True)
    px = f.close_us_cents_per_lb.astype(float).where(D.usable).ffill()
    return pd.DataFrame({"px": px, "roll": f.suspected_roll_flag.astype(str).str.lower().eq("true"),
                         "volume": pd.to_numeric(f.volume_vendor, errors="coerce")}, index=D.dates.index)


def roll_carry(D, k=4, offset=0):
    """Carry from the price gap at a roll: minus the mean raw log return of the last k gap days.
    offset 0 = the marked roll day (c02; shown later to be the wrong day), offset 1 = the next session, where
    the gap between contracts is. Positive = backwardation (the next contract is cheaper than the old one)."""
    f = raw_px(D)
    gap = np.log(f.px).diff().where(f.roll.shift(offset, fill_value=False))
    c = -gap.dropna().rolling(k, min_periods=k).mean()
    return c.reindex(D.dates.index).ffill().rename(f"carry{k}" + ("n" if offset else ""))


def value(D, n=1260):
    """Log raw front-month price minus its mean of the last n sessions (negative = cheap against history)."""
    lp = np.log(raw_px(D).px)
    return (lp - lp.rolling(n, min_periods=n).mean()).rename(f"value{n}")


def bra_wx(D, n=90, lag=4):
    """Brazil (output-weighted) rain and temperature z-scores, mean of the last n days, at t - lag days."""
    c = country_z(D)[["rain_bra", "temp_bra"]]
    return D.align_daily(c.rolling(n, min_periods=n).mean(), lag).rename(columns=lambda x: f"{x}{n}")


def tri_fp(col, lo, hi, sign=1.0):
    """Unfitted three-state rule: probability 1 if sign*x > hi, 0 if sign*x < lo, else 0.5 (steady)."""
    def fp(Xtr, ytr, gtr, Xte, seed):
        x = sign * Xte[col].to_numpy(float)
        return np.where(x > hi, 1.0, np.where(x < lo, 0.0, 0.5))
    return fp


def bra_stress(D, n=90, detrend=1825, lag=4):
    """Brazil heat-and-dry stress: (temperature z - rain z), mean of n days, minus its own trailing mean of
    `detrend` days (removes the slow climate drift), at t - lag days."""
    c = country_z(D)
    s = (c.temp_bra - c.rain_bra).rolling(n, min_periods=n).mean()
    s = s - s.rolling(detrend, min_periods=detrend).mean()
    return D.align_daily(s.to_frame(f"stress_bra{n}"), lag)


def cot_z(D, weeks=104):
    """Managed-money net share of open interest, z-score against its own last `weeks` reports."""
    t = D.cot()
    t["mm_z"] = (t.mm_net_share - t.mm_net_share.rolling(weeks, min_periods=weeks).mean()) / \
        t.mm_net_share.rolling(weeks, min_periods=weeks).std(ddof=1)
    return D.align_avail(t, ["mm_z"], 14)


OTHER = ["col", "eth", "gua", "hon", "mex"]      # filled from the node file at run time (see other_stress)


def other_stress(D, n=90, detrend=1825, lag=4):
    """Mean heat-and-dry stress of all origins except Brazil (simple mean of the country means), drift removed."""
    c = country_z(D)
    tags = sorted({x.split("_")[1] for x in c.columns} - {"bra"})
    s = sum(c[f"temp_{t}"] - c[f"rain_{t}"] for t in tags) / len(tags)
    s = s.rolling(n, min_periods=n).mean()
    s = s - s.rolling(detrend, min_periods=detrend).mean()
    return D.align_daily(s.to_frame(f"stress_oth{n}"), lag)


def bra_frost(D, n=90, lag=4):
    """Frost depth in the Brazil regions: max(0, 5 C - lowest minimum temperature of the 6 regions), Jun-Aug
    only; the largest value of the last n days, at t - lag days."""
    t = D.weather_raw("temperature_min_c")[list(BRAZIL_W)].min(axis=1, skipna=False)
    f = (5.0 - t).clip(lower=0).where(t.index.month.isin([6, 7, 8]), 0.0)
    return D.align_daily(f.rolling(n, min_periods=n).max().to_frame(f"frost_bra{n}"), lag)


def clim_anom(s, n=90, years=5):
    """Mean of the last n days minus the mean of the same quantity 1..years years before (seasonal normal of
    the recent climate). Uses earlier data only."""
    m = s.rolling(n, min_periods=n).mean()
    return m - sum(m.shift(365 * k) for k in range(1, years + 1)) / years


def bra_extra(D, col, n=90, years=5, lag=4):
    """Brazil output-weighted POWER variable from new source 1 (gwetroot, rh2m, srad): mean of n days minus the
    seasonal normal of the last `years` years, at t - lag days."""
    w = pd.Series(BRAZIL_W) / sum(BRAZIL_W.values())
    x = (D.weather_raw(col, file="power_extra.csv")[list(w.index)] * w).sum(axis=1, skipna=False)
    return D.align_daily(clim_anom(x, n, years).to_frame(f"{col}_bra{n}"), lag)


def mkt_ret(D, name, n=63):
    """n-session log return of another market (closes strictly before t)."""
    x = D.align_prev(D.market_daily(name))
    return (x - x.shift(n)).rename(f"{name}_ret{n}")


def signals4(D):
    """The four features with a mechanism and a positive score as single rules (c06, c11, c09, c13)."""
    return bra_stress(D, 90).join(bra_extra(D, "gwetroot", 90)).join(other_stress(D, 90)).join(mkt_ret(D, "dxy", 63))


def wide16(D):
    """16 features for the tree models: 6 weather, 7 price, 2 currency, 1 ENSO. Training can start in 2001."""
    p = price_feats(D)[["kret21", "kret63", "kret252", "lrv63", "sin_doy", "cos_doy"]]
    return (bra_stress(D, 90).join(bra_extra(D, "gwetroot", 90)).join(bra_extra(D, "rh2m", 90))
            .join(bra_extra(D, "srad", 90)).join(other_stress(D, 90)).join(bra_frost(D, 90)).join(p)
            .join(roll_carry(D, 4, offset=1)).join(mkt_ret(D, "dxy", 63)).join(brl_feats(D)[["brl_ret63"]])
            .join(enso2(D)[["enso_lvl"]]))


WIDE_ALT = ["stress_bra90", "gwetroot_bra90", "rh2m_bra90", "srad_bra90", "stress_oth90", "frost_bra90", "enso_lvl"]


def season_mean(x, months=(10, 11, 12, 1, 2, 3, 4), start_month=10, min_days=30):
    """Season-to-date mean of a daily series over the growing months (season starts in `start_month`).
    Outside the growing months, and in the first `min_days` of a season, the last value is held."""
    idx = x.index
    season = np.where(idx.month >= start_month, idx.year, idx.year - 1)
    inseason = pd.Series(idx.month.isin(months), index=idx)
    xs = x.where(inseason)
    cnt = xs.notna().groupby(season).cumsum()
    s = (xs.fillna(0.0).groupby(season).cumsum() / cnt.where(cnt >= min_days)).where(inseason & xs.notna())
    return s.ffill()


def bra_season_stress(D, years=5, lag=4, which="stress"):
    """Brazil stress of the crop season to date (Oct-Apr), minus the same quantity 1..years years before."""
    c = country_z(D)
    x = {"stress": c.temp_bra - c.rain_bra, "rain": -c.rain_bra, "temp": c.temp_bra}[which]
    s = season_mean(x)
    a = s - sum(s.shift(365 * k) for k in range(1, years + 1)) / years
    return D.align_daily(a.to_frame(f"season_{which}_bra"), lag)


def bra_season_raw(D, col="temperature_max_c", years=5, lag=4, file="power_daily_arabica_world.csv", name=None,
                   memory=False):
    """Brazil output-weighted raw POWER variable: crop-season-to-date mean (Oct-Apr, held May-Sep) minus the
    same quantity 1..years years before."""
    w = pd.Series(BRAZIL_W) / sum(BRAZIL_W.values())
    x = (D.weather_raw(col, file=file)[list(w.index)] * w).sum(axis=1, skipna=False)
    s = season_mean(x)
    a = s - sum(s.shift(365 * k) for k in range(1, years + 1)) / years
    if memory:                                      # c26: mean of this season's and the previous season's anomaly
        a = (a + a.shift(365)) / 2
    return D.align_daily(a.to_frame(name or f"season_{col}"), lag)


def usda_stocks(D, k=5):
    """World coffee ending stocks / domestic consumption (USDA PSD, marketing years from 2002), minus the mean
    of the k marketing years before. Year Y is used from 1 Oct Y+2 (plan: 12 months after the year ended)."""
    global _PSD
    if _PSD is None:
        _PSD = pd.read_csv(Path(__file__).resolve().parent / "data" / "raw_psd" / "psd_coffee.csv")
    d = _PSD[_PSD.Attribute_Description.isin(["Ending Stocks", "Domestic Consumption"]) & (_PSD.Market_Year >= 2002)]
    w = d.groupby(["Market_Year", "Attribute_Description"]).Value.sum().unstack()
    t = pd.DataFrame({"my": w.index, "stu": (w["Ending Stocks"] / w["Domestic Consumption"]).to_numpy()})
    t["stu_dev"] = t.stu - t.stu.shift(1).rolling(k, min_periods=k).mean()
    t["avail"] = pd.to_datetime((t.my + 2).astype(str) + "-10-01")
    t = t[t.avail <= D.cutoff]
    return D.align_avail(t, ["stu_dev"], 400)


_PSD = None


def mkt_rets(D, names, n=126):
    """n-session log returns of several other markets (closes strictly before t), one column each."""
    return pd.concat([mkt_ret(D, k, n) for k in names], axis=1)


def vote_fp(k=None):
    """Unfitted vote: probability 1 if at least k columns are > 0 (default: a strict majority), else 0."""
    def fp(Xtr, ytr, gtr, Xte, seed):
        need = k if k is not None else Xte.shape[1] // 2 + 1
        return ((Xte.to_numpy(float) > 0).sum(axis=1) >= need).astype(float)
    return fp


def season_flag(D, early=(2, 3, 4, 5), late=(6, 7, 8, 9)):
    """Calendar feature: +1 in the `early` months, -1 in the `late` months, 0 in the others."""
    m = D.dates.dt.month
    return pd.Series(np.where(m.isin(early), 1.0, np.where(m.isin(late), -1.0, 0.0)), index=D.dates.index, name="season")


def season_raw_nodes(D, ids, col="temperature_max_c", years=5, lag=4, name="season_x", months=(10, 11, 12, 1, 2, 3, 4),
                     start_month=10, file="power_daily_arabica_world.csv", w=None):
    """Season-to-date mean of a raw POWER variable over a list of nodes (simple mean, or weights w), minus
    the same quantity 1..years years before. Same construction as bra_season_raw, other places."""
    t = D.weather_raw(col, file=file)[list(ids)]
    x = (t * pd.Series(w)).sum(axis=1, skipna=False) if w is not None else t.mean(axis=1, skipna=False)
    s = season_mean(x, months=months, start_month=start_month)
    a = s - sum(s.shift(365 * k) for k in range(1, years + 1)) / years
    return D.align_daily(a.to_frame(name), lag)


def monthly_anom(D, name, k=3, years=5, log=True, col=None, tol_days=45):
    """Monthly series: mean of the last k months (log if `log`) minus the same quantity in the same month of
    the last `years` years. Aligned by the publication date of the card."""
    t = D.monthly(name)
    assert t.month.diff().dropna().dt.days.between(28, 31).all(), f"{name}: months are missing in the file"
    v = np.log(t.value) if log else t.value
    m = v.rolling(k, min_periods=k).mean()
    col = col or f"{name}_anom"
    t[col] = m - sum(m.shift(12 * j) for j in range(1, years + 1)) / years
    return D.align_avail(t, [col], tol_days)


_COT = None


def hedge_pressure(D, weeks=104):
    """Producer/merchant net SHORT position as a share of open interest (CFTC disaggregated report), z-score
    against its own last `weeks` reports. Available 6 days after the report date (as in the project)."""
    global _COT
    if _COT is None:
        raw = pd.read_csv(Path(__file__).resolve().parent.parent / "data" / "cftc" / "cftc_coffee_c_disaggregated_72hh-3qpy.csv", low_memory=False)
        raw = raw[raw.market_and_exchange_names.astype(str).str.upper().str.contains("COFFEE C")]
        _COT = pd.DataFrame({"report": pd.to_datetime(raw.report_date_as_yyyy_mm_dd.astype(str).str[:10]),
                             "hp": (pd.to_numeric(raw.prod_merc_positions_short) - pd.to_numeric(raw.prod_merc_positions_long))
                             / pd.to_numeric(raw.open_interest_all)}).drop_duplicates("report").sort_values("report").reset_index(drop=True)
    t = _COT.copy()
    t["avail"] = t.report + pd.Timedelta(days=6)
    t = t[t.avail <= D.cutoff].reset_index(drop=True)
    if D.rot:
        t["hp"] = np.roll(t.hp.to_numpy(), D.rot * 52)
    t["hp_z"] = (t.hp - t.hp.rolling(weeks, min_periods=weeks).mean()) / t.hp.rolling(weeks, min_periods=weeks).std(ddof=1)
    return D.align_avail(t, ["hp_z"], 14)


def wx22(D, lag=4):
    """The two features of the current best c22: season maximum-temperature anomaly and 90-day stress."""
    return bra_season_raw(D, "temperature_max_c", name="season_tmax", lag=lag).join(bra_stress(D, 90, lag=lag))


def w22(X):
    """Position of c22 from its two features: +1 both > 0, -1 both < 0, else 0."""
    a, b = X.season_tmax.to_numpy(float), X.stress_bra90.to_numpy(float)
    return np.where((a > 0) & (b > 0), 1.0, np.where((a < 0) & (b < 0), -1.0, 0.0))


def trend5(D):
    """Five market-trend signs with a mechanism (positive = supports a higher coffee price): sugar, Brazil
    equities and copper 126-session returns, minus the dollar index 63-session return, coffee 252-session return."""
    x = mkt_rets(D, ["sugar", "ewz", "copper"], 126)
    x["dxy_down63"] = -mkt_ret(D, "dxy", 63)
    x["kret252"] = D.L - D.L.shift(252)
    return x


def bra_window_tmax(D, months, start_month, name, years=5, lag=4):
    """Brazil output-weighted maximum temperature: mean to date over the given months (held until the window
    opens again), minus the same quantity of the last `years` years."""
    w = pd.Series(BRAZIL_W) / sum(BRAZIL_W.values())
    return season_raw_nodes(D, list(w.index), months=months, start_month=start_month, name=name, years=years, lag=lag, w=w)


def bra_window_var(D, col, months, start_month, name, years=5, lag=4, ids=None, file="power_daily_arabica_world.csv"):
    """Like bra_window_tmax for another variable or a subset of the Brazil regions (weights re-scaled)."""
    w = pd.Series(BRAZIL_W)
    if ids is not None:
        w = w[list(ids)]
    w = w / w.sum()
    return season_raw_nodes(D, list(w.index), col=col, months=months, start_month=start_month, name=name, years=years,
                            lag=lag, w=w, file=file)


def brl_price_dev(D, n=252):
    """Log coffee price in Brazilian reais (raw front-month price x USD/BRL of t-1) minus its mean of n sessions."""
    lp = np.log(raw_px(D).px) + D.align_prev(D.market_daily("usd_brl"))
    return (lp - lp.rolling(n, min_periods=n).mean()).rename("brl_price_dev")


def best4(D):
    """Four features of the rules with skill: grain-fill mean-temperature anomaly (c52), 90-day stress (c06),
    Vietnam dry-season heat (c55), number of rising markets in the five-market composite (c42)."""
    x = bra_window_var(D, "temperature_mean_c", (1, 2, 3), 1, "fill_tmean").join(bra_stress(D, 90))
    x = x.join(season_raw_nodes(D, ["vn_dak_lak", "vn_lam_dong", "vn_gia_lai"], months=(1, 2, 3, 4), start_month=1,
                                name="vn_dry_tmax", file="power_vietnam.csv"))
    t = trend5(D)
    x["trend_votes"] = (t > 0).sum(axis=1).where(t.notna().all(axis=1))
    return x


def logit_decay_fp(C=1.0, half_life_years=3.0):
    """Logistic regression with time-decay weights: a training row that is `half_life_years` older than the
    newest training row has half its weight. Uses training rows only."""
    def fp(Xtr, ytr, gtr, Xte, seed):
        age = (len(Xtr) - 1 - np.arange(len(Xtr))) / 252.0
        w = 0.5 ** (age / half_life_years)
        sc = StandardScaler().fit(Xtr)
        m = LogisticRegression(C=C, solver="lbfgs", max_iter=2000, tol=1e-8).fit(sc.transform(Xtr), ytr, sample_weight=w)
        return m.predict_proba(sc.transform(Xte))[:, 1]
    return fp


def level_dev(D, name, n=252):
    """Log level of another market (through t-1) minus its mean of n sessions."""
    x = D.align_prev(D.market_daily(name))
    return (x - x.rolling(n, min_periods=n).mean()).rename(f"{name}_dev{n}")


def agree_fp(cols, signs=None):
    """Three-state agreement of sign rules: +1 if all (signed) columns > 0, -1 if all < 0, else steady."""
    def fp(Xtr, ytr, gtr, Xte, seed):
        x = Xte[list(cols)].to_numpy(float) * (np.asarray(signs, float) if signs is not None else 1.0)
        return np.where((x > 0).all(axis=1), 1.0, np.where((x < 0).all(axis=1), 0.0, 0.5))
    return fp

TR5 = ["sugar_ret126", "ewz_ret126", "copper_ret126", "dxy_down63", "kret252"]


def vn_heat(D, lag=4):
    return season_raw_nodes(D, ["vn_dak_lak", "vn_lam_dong", "vn_gia_lai"], months=(1, 2, 3, 4), start_month=1,
                            name="vn_dry_tmax", file="power_vietnam.csv", lag=lag)


def trend_sign(X):
    """+1 if three or more of the five market trends are positive, else -1."""
    return np.where((X[TR5].to_numpy(float) > 0).sum(axis=1) >= 3, 1.0, -1.0)


def sum_fp(parts):
    """Position = sign of the sum of the parts (each a function X -> array of -1/0/+1); 0 gives steady."""
    def fp(Xtr, ytr, gtr, Xte, seed):
        t = sum(p(Xte) for p in parts)
        return np.where(t > 0, 1.0, np.where(t < 0, 0.0, 0.5))
    return fp


def monthly_chg(D, name, k=3, col=None, tol_days=45):
    """k-month log change of a monthly series, aligned by the publication date of its card."""
    t = D.monthly(name)
    assert t.month.diff().dropna().dt.days.between(28, 31).all(), f"{name}: months are missing in the file"
    col = col or f"{name}_chg{k}"
    t[col] = np.log(t.value) - np.log(t.value.shift(k))
    return D.align_avail(t, [col], tol_days)


def vol_filter_fp(pos_fn, col="lrv21", q=200 / 3):
    """Position of pos_fn, set to steady when the volatility feature is above the q-th percentile of the
    training rows (volatility-managed exposure with positions -1/0/+1)."""
    def fp(Xtr, ytr, gtr, Xte, seed):
        thr = np.percentile(Xtr[col].to_numpy(float), q)
        p = np.where(Xte[col].to_numpy(float) > thr, 0.0, pos_fn(Xte))
        return (p + 1) / 2
    return fp


def trend_n(D, n):
    """The five-market composite with one horizon n for all markets (dollar sign reversed)."""
    x = mkt_rets(D, ["sugar", "ewz", "copper"], n)
    x[f"dxy_down{n}"] = -mkt_ret(D, "dxy", n)
    x[f"kret{n}"] = D.L - D.L.shift(n)
    return x


def origin_heat(D, countries, months, start_month, name, lag=4, col="temperature_max_c"):
    """Heat of the critical crop window in other origins: mean maximum temperature of the window to date over
    all nodes of the given countries (held until the window opens again), minus the last 5 years."""
    n = D.nodes()
    return season_raw_nodes(D, list(n.index[n.country.isin(countries)]), col=col, months=months, start_month=start_month,
                            name=name, lag=lag)


def jfm_specific(D, lag=4):
    """Brazil-specific grain-fill heat: Brazil Jan-Mar maximum-temperature anomaly minus the same anomaly of
    all other nodes of the project (the common tropical part)."""
    n = D.nodes()
    b = bra_window_tmax(D, (1, 2, 3), 1, "x", lag=lag).x
    o = season_raw_nodes(D, list(n.index[n.country != "Brazil"]), months=(1, 2, 3), start_month=1, name="x", lag=lag).x
    return pd.DataFrame({"bra_minus_others": b - o, "others_jfm": o})


def enso_jan(D):
    """Nino 3.4 anomaly of the latest January (published mid February), held until the next January value."""
    t = D.monthly("nino34")
    t = t[t.month.dt.month == 1].copy()
    t["enso_jan"] = t.value
    return D.align_avail(t, ["enso_jan"], 400)


def three(D):
    """ENSO January value, Brazil grain-fill mean-temperature anomaly, number of rising markets (0-5)."""
    x = enso_jan(D).join(bra_window_var(D, "temperature_mean_c", (1, 2, 3), 1, "fill_tmean"))
    t = trend5(D)
    x["trend_votes"] = (t > 0).sum(axis=1).where(t.notna().all(axis=1))
    return x


def era5_water_balance(D, months=(1, 2, 3), start_month=1, years=5, lag=7, name="fill_wb_era5"):
    """Brazil output-weighted climatic water balance (rain minus reference evapotranspiration, ERA5): mean of
    the window to date, held until the window opens again, minus the last `years` years."""
    w = pd.Series(BRAZIL_W) / sum(BRAZIL_W.values())
    x = ((D.weather_raw("rain", file="era5_brazil.csv") - D.weather_raw("et0", file="era5_brazil.csv"))[list(w.index)] * w).sum(axis=1, skipna=False)
    s = season_mean(x, months=months, start_month=start_month)
    a = s - sum(s.shift(365 * k) for k in range(1, years + 1)) / years
    return D.align_daily(a.to_frame(name), lag)


def three_sum(heat="fill_tmean"):
    """Majority of ENSO January sign, a Brazil heat sign, and the five-market trend vote."""
    return sum_fp([lambda X: np.sign(X.enso_jan.to_numpy(float)), lambda X: np.sign(X[heat].to_numpy(float)), trend_sign])


def enso_djf(D):
    """Mean Nino 3.4 anomaly of December-February (complete with the February value, published mid March),
    held until the next winter value."""
    t = D.monthly("nino34")
    t["enso_djf"] = t.value.rolling(3, min_periods=3).mean()
    t = t[t.month.dt.month == 2]
    return D.align_avail(t, ["enso_djf"], 400)


def two_state(D, col="temperature_mean_c", months=(1, 2, 3), start_month=1, years=5, lag=10, ids=None, file="power_daily_arabica_world.csv"):
    """Inputs of the two-state rule c86: January Nino 3.4 and a Brazil heat anomaly (settings as arguments)."""
    return enso_jan(D).join(bra_window_var(D, col, months, start_month, "fill_heat", years=years, lag=lag, ids=ids, file=file))


def two_state_both(D, lag=10):
    """c93: January Nino 3.4 and the mean of two Brazil Jan-Mar mean-temperature anomalies (NASA POWER and
    ERA5), each divided by its own expanding standard deviation (earlier values only)."""
    a = bra_window_var(D, "temperature_mean_c", (1, 2, 3), 1, "a", lag=lag).a
    b = bra_window_var(D, "tmean", (1, 2, 3), 1, "b", lag=lag, file="era5_brazil.csv").b
    z = lambda s: s / s.expanding(min_periods=756).std(ddof=1)
    return enso_jan(D).join(((z(a) + z(b)) / 2).rename("fill_heat"))


def enso_latest(D):
    """Nino 3.4 of the latest January or July (published mid February / mid August), held until the next one."""
    t = D.monthly("nino34")
    t = t[t.month.dt.month.isin([1, 7])].copy()
    t["enso_jj"] = t.value
    return D.align_avail(t, ["enso_jj"], 220)


def final_inputs(D, lag=10):
    """December-February Nino 3.4 mean and the two-product Brazil Jan-Mar heat (c99, c100)."""
    return enso_djf(D).join(two_state_both(D, lag=lag)[["fill_heat"]])
