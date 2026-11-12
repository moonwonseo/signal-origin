"""V5 spike labels: V4's crossing rule with the threshold as a parameter.

`threshold_labels(frame, h, 10)` reproduces `freight.labels(frame, h)` exactly (tested). The only
additions are (1) `threshold_pct`, and (2) an optional `crossing_eligible` mask for the
pre-declared label-sensitivity run, in which a crossing counts only on eligible sessions
(e.g. reported volume >= 1,000 and not a roll day). Window completeness is unchanged: every
price in t+1..t+h must still be usable, so the mask never shortens or compresses a window.
"""
from decimal import Decimal, InvalidOperation, localcontext

import numpy as np
import pandas as pd

Y = "target_spike"


def threshold_labels(frame: pd.DataFrame, h: int, threshold_pct: int = 10,
                     crossing_eligible: pd.Series | None = None) -> pd.DataFrame:
    if type(h) is not int or h < 1:
        raise ValueError("horizon must be a positive integer")
    if type(threshold_pct) is not int or not 1 <= threshold_pct <= 100:
        raise ValueError("threshold_pct must be an integer percentage from 1 to 100")
    req = {"price_date", "session_index", "price_usable", "raw_price_text"}
    if not req.issubset(frame):
        raise ValueError("Missing label input columns")
    n = len(frame)
    if not np.array_equal(frame.session_index.to_numpy(), np.arange(n)):
        raise ValueError("Do not compress the session calendar")
    dates = frame.price_date
    if (not pd.api.types.is_datetime64_any_dtype(dates) or dates.isna().any()
            or dates.duplicated().any() or not dates.is_monotonic_increasing):
        raise ValueError("Invalid session dates")
    if not pd.api.types.is_bool_dtype(frame.price_usable) or frame.price_usable.isna().any():
        raise ValueError("Use explicit price usability booleans")
    if crossing_eligible is None:
        eligible = [True] * n
    else:
        if len(crossing_eligible) != n or crossing_eligible.isna().any():
            raise ValueError("crossing_eligible must cover every session with a boolean")
        eligible = [bool(x) for x in crossing_eligible]
    p = []
    for ok, s in zip(frame.price_usable, frame.raw_price_text):
        if not ok:
            p.append(None)
            continue
        try:
            v = Decimal(str(s))
        except (InvalidOperation, ValueError) as e:
            raise ValueError("Bad price") from e
        if not v.is_finite() or v <= 0:
            raise ValueError("Price must be finite and positive")
        p.append(v)
    hundred, bar = Decimal(100), Decimal(100 + threshold_pct)
    out, first, peak = [None] * n, [pd.NaT] * n, [None] * n
    with localcontext() as ctx:
        ctx.prec = 80
        for i in range(max(0, n - h)):
            w = p[i + 1:i + h + 1]
            if p[i] is None or any(v is None for v in w):
                continue
            peak[i] = str(max(w))
            cross = next((j for j, v in enumerate(w, 1)
                          if eligible[i + j] and hundred * v >= bar * p[i]), None)
            out[i] = int(cross is not None)
            if cross is not None:
                first[i] = dates.iloc[i + cross]
    return pd.DataFrame({Y: pd.array(out, dtype="Int64"), "label_end_date": dates.shift(-h),
                         "first_cross_date": pd.to_datetime(first),
                         "future_max_close_audit_only": peak}, index=frame.index)
