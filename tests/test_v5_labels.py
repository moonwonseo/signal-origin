"""V5 labels: threshold 10 must equal V4 exactly; masks and thresholds behave monotonically."""
import pandas as pd
import pytest

from signal_origin import freight as v4
from signal_origin.synthetic_v4 import make_inputs
from signal_origin.v5_labels import threshold_labels


@pytest.fixture(scope="module")
def frame():
    return make_inputs()[0].frame


@pytest.mark.parametrize("h", [21, 63])
def test_threshold_10_reproduces_v4_exactly(frame, h):
    pd.testing.assert_frame_equal(threshold_labels(frame, h, 10), v4.labels(frame, h))


def test_higher_threshold_never_adds_positives(frame):
    y = {t: threshold_labels(frame, 63, t)["target_spike"] for t in (5, 10, 15)}
    ready = y[10].notna()
    assert (y[15][ready] <= y[10][ready]).all() and (y[10][ready] <= y[5][ready]).all()
    assert y[5][ready].sum() > y[15][ready].sum()


def test_mask_only_removes_positives_and_keeps_windows(frame):
    full = threshold_labels(frame, 63, 10)
    mask = pd.Series([i % 3 != 0 for i in range(len(frame))], index=frame.index)
    masked = threshold_labels(frame, 63, 10, crossing_eligible=mask)
    assert full.target_spike.isna().equals(masked.target_spike.isna())
    ready = full.target_spike.notna()
    assert (masked.target_spike[ready] <= full.target_spike[ready]).all()
    crossed = masked.first_cross_date.dropna()
    pos = frame.set_index("price_date").index.get_indexer(crossed)
    assert mask.iloc[pos].all()


def test_bad_threshold_rejected(frame):
    with pytest.raises(ValueError):
        threshold_labels(frame, 63, 0)
