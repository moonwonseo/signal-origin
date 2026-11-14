"""Timing and parsing checks with artificial data (no real CFTC or ICE data)."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pos_study as ps
from signal_origin.synthetic_v4 import make_inputs


def fake_cot(tmp, style="api"):
    tues = pd.date_range("2018-01-02", "2026-10-06", freq="7D")
    rng = np.random.default_rng(2)
    oi = rng.integers(150_000, 300_000, len(tues))
    lg, sh = rng.integers(10_000, 80_000, len(tues)), rng.integers(10_000, 80_000, len(tues))
    if style == "api":
        cols = {"market_and_exchange_names": "COFFEE C - ICE FUTURES U.S.",
                "report_date_as_yyyy_mm_dd": tues.strftime("%Y-%m-%dT00:00:00.000"),
                "open_interest_all": oi, "m_money_positions_long_all": lg, "m_money_positions_short_all": sh}
    else:  # CFTC yearly text-file header style
        cols = {"Market_and_Exchange_Names": "COFFEE C - ICE FUTURES U.S.",
                "Report_Date_as_YYYY-MM-DD": tues.strftime("%Y-%m-%d"),
                "Open_Interest_All": oi, "M_Money_Positions_Long_All": lg, "M_Money_Positions_Short_All": sh}
    df = pd.DataFrame(cols)
    other = df.copy(); other.iloc[:, 0] = "COCOA - ICE FUTURES U.S."
    p = tmp / f"cot_{style}.csv"; pd.concat([df, other]).to_csv(p, index=False)
    return p


def test_both_header_styles_parse_and_keep_only_coffee(tmp_path):
    a, b = ps.load_cot(fake_cot(tmp_path, "api")), ps.load_cot(fake_cot(tmp_path, "txt"))
    pd.testing.assert_frame_equal(a, b)
    assert a.report_date.is_unique


def test_cot_used_only_after_following_monday(tmp_path):
    cot = ps.load_cot(fake_cot(tmp_path))
    dates = pd.Series(pd.bdate_range("2019-01-01", "2019-03-01"))
    m = ps.align_cot(dates, cot)
    used = m.dropna(subset=["report_date"])
    assert (used.price_date - used.report_date >= pd.Timedelta(days=6)).all()
    tue = pd.Timestamp("2019-01-15")                     # a report date
    assert m.loc[m.price_date.eq(pd.Timestamp("2019-01-18")), "report_date"].iloc[0] < tue   # Friday: not yet
    assert m.loc[m.price_date.eq(pd.Timestamp("2019-01-21")), "report_date"].iloc[0] == tue  # Monday: yes


def test_stocks_used_from_next_session(tmp_path):
    days = pd.bdate_range("2015-01-01", "2016-12-31")
    p = tmp_path / "s.csv"
    pd.DataFrame({"Date": days, "Bags": np.linspace(1e6, 2e5, len(days))}).to_csv(p, index=False)
    s = ps.load_stocks(p)
    m = ps.align_stocks(pd.Series(days[100:110]), s)
    assert (m.stock_date < m.price_date).all()


def test_end_to_end_runs_on_artificial_data(tmp_path):
    inp, _, _ = make_inputs()
    frame = inp.frame
    cot = ps.load_cot(fake_cot(tmp_path))
    base, r = ps.base_frame(frame, cot=cot)
    spikes, vol, _, _ = ps.run_source(frame, base, r, ps.POS, "GP", years=range(2024, 2026),
                                      train_start="2019-01-02", cells=((10, 63),))
    assert set(spikes.model) == {"B0", "V0", "G", "GP"} and not vol.empty
