from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from signal_origin.io import load_inputs, write_json
from signal_origin.synthetic import synthetic_frames
from signal_origin.spec import RunConfig


def write_case(folder: Path, n=900, seed=42):
    folder.mkdir(parents=True, exist_ok=True)
    prices, sessions, meta = synthetic_frames(n, seed)
    paths = {"prices": folder / "SYNTHETIC_prices.csv", "sessions": folder / "SYNTHETIC_sessions.csv", "metadata": folder / "SYNTHETIC_metadata.json"}
    prices.to_csv(paths["prices"], index=False)
    sessions.to_csv(paths["sessions"], index=False)
    write_json(paths["metadata"], meta)
    return paths


def prepared_frame(values, dates=None):
    if dates is None:
        dates = pd.bdate_range("2020-01-02", periods=len(values))
    numbers = [np.nan if v is None else float(v) for v in values]
    usable = np.isfinite(numbers)
    return pd.DataFrame({"price_date": pd.to_datetime(dates), "session_index": np.arange(len(values)),
        "close_us_cents_per_lb": numbers, "model_price": numbers,
        "price_usable": usable, "quality_status": np.where(usable, "ok", "missing"),
        "raw_price_text": ["" if v is None else str(v) for v in values]})


@pytest.fixture
def paths(tmp_path):
    return write_case(tmp_path / "input")


@pytest.fixture
def inputs(paths):
    return load_inputs(**paths)


@pytest.fixture
def config(inputs):
    return RunConfig(test_start=inputs.frame.price_date.iloc[600].strftime("%Y-%m-%d"),
                     test_end=inputs.frame.price_date.iloc[800].strftime("%Y-%m-%d"))
