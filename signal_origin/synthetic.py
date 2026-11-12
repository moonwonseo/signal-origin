"""Artificial mechanics-test data, NEVER historical coffee observations."""
from pathlib import Path
import numpy as np
import pandas as pd
from .io import write_json
from .spec import SignalOriginError


def synthetic_frames(n: int = 1800, seed: int = 42) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    if type(n) is not int or n < 200:
        raise SignalOriginError("Synthetic fixture requires at least 200 rows.")
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2010-01-04", periods=n)
    i = np.arange(n, dtype=float)
    log_returns = 0.0001 + 0.0035 * np.sin(2 * np.pi * i / 220) + rng.normal(0, 0.012, n)
    price = 100 * np.exp(np.cumsum(log_returns))
    prices = pd.DataFrame({"price_date": dates.strftime("%Y-%m-%d"),
                           "close_us_cents_per_lb": np.round(price, 6),
                           "quality_status": "ok"})
    sessions = pd.DataFrame({"session_date": dates.strftime("%Y-%m-%d")})
    meta = {
        "data_kind": "synthetic", "instrument": "SYNTHETIC_TEST_SERIES",
        "frequency": "exchange_session", "price_units": "us_cents_per_lb", "price_field": "close",
        "source_name": "Artificial deterministic software-test generator; NOT market data",
        "source_url": "synthetic://signal-origin/software-tests",
        "retrieved_at_utc": "2026-10-12T00:00:00Z",
        "calendar_source": "Artificial Monday-Friday sequence; NOT the ICE exchange calendar",
        "calendar_verified": True,
        "roll_adjustment_status": "documented_return_compatible",
        "series_construction": "Artificial price path; no futures contracts and no real roll adjustments. Flags satisfy only synthetic test gates.",
        "point_in_time_status": "synthetic_not_applicable",
        "notes": "SYNTHETIC SOFTWARE TEST ONLY. The units and dates are fixture conventions, not historical observations. This data cannot establish forecasting skill."
    }
    return prices, sessions, meta


def write_synthetic_inputs(folder: Path, n: int = 1800, seed: int = 42) -> dict[str, Path]:
    folder.mkdir(parents=True, exist_ok=False)
    prices, sessions, meta = synthetic_frames(n=n, seed=seed)
    paths = {"prices": folder / "SYNTHETIC_prices.csv", "sessions": folder / "SYNTHETIC_sessions.csv", "metadata": folder / "SYNTHETIC_metadata.json"}
    prices.to_csv(paths["prices"], index=False)
    sessions.to_csv(paths["sessions"], index=False)
    write_json(paths["metadata"], meta)
    return paths
