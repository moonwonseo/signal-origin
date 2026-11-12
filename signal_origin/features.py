"""Causal trailing features and the fixed 63-session endpoint label."""
from decimal import Decimal, localcontext
import numpy as np
import pandas as pd

from .spec import FEATURES, HORIZON


def feature_frame(frame: pd.DataFrame) -> pd.DataFrame:
    """No fit or global statistic. Each feature at t uses only prices through t.

    vol63 is the sample standard deviation of 63 daily SIMPLE returns,
    ddof=1, NOT annualized. No forward filling and no centered windows.
    """
    price = frame["model_price"].astype(float)
    daily_return = price.pct_change(fill_method=None)
    dates = frame["price_date"]
    days_in_year = np.where(dates.dt.is_leap_year, 366.0, 365.0)
    phase = (dates.dt.dayofyear.to_numpy() - 1) / days_in_year
    out = pd.DataFrame(index=frame.index)
    out["ret21"] = price.pct_change(periods=21, fill_method=None)
    out["ret63"] = price.pct_change(periods=63, fill_method=None)
    out["vol63"] = daily_return.rolling(63, min_periods=63).std(ddof=1)
    out["sin_doy"] = np.sin(2 * np.pi * phase)
    out["cos_doy"] = np.cos(2 * np.pi * phase)
    # Avoid treating overflows as valid features.
    return out.loc[:, list(FEATURES)].replace([np.inf, -np.inf], np.nan)


def endpoint_labels(frame: pd.DataFrame) -> pd.DataFrame:
    """Decimal price strings make the inclusive threshold exact at source precision.

    Using 100*P[t+63] >= 110*P[t] avoids a floating-point boundary error.
    Interior future missing prices do not change an endpoint label if both
    endpoint prices exist: the explicit calendar still fixes session t+63.
    """
    n = len(frame)
    labels: list[int | None] = [None] * n
    usable = frame["price_usable"].to_numpy(dtype=bool)
    text = frame["raw_price_text"].tolist()
    with localcontext() as ctx:
        ctx.prec = 80
        for i in range(max(0, n - HORIZON)):
            j = i + HORIZON
            if usable[i] and usable[j]:
                now, later = Decimal(text[i]), Decimal(text[j])
                labels[i] = int(later * Decimal(100) >= now * Decimal(110))
    out = pd.DataFrame(index=frame.index)
    out["label_end_date"] = frame["price_date"].shift(-HORIZON)
    out["future_price_63"] = frame["model_price"].shift(-HORIZON)
    out["target_up_10pct_63_sessions"] = pd.array(labels, dtype="Int64")
    return out


def build_design(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep every expected session; exclusion happens AFTER features and labels."""
    columns = ["price_date", "session_index", "close_us_cents_per_lb", "quality_status", "price_usable"]
    design = frame.loc[:, columns].copy()
    design = pd.concat([design, feature_frame(frame), endpoint_labels(frame)], axis=1)
    design["features_ready"] = np.isfinite(design.loc[:, list(FEATURES)].to_numpy(dtype=float)).all(axis=1)
    design["label_ready"] = design["target_up_10pct_63_sessions"].notna()
    design["eligible"] = design["features_ready"] & design["label_ready"]
    return design
