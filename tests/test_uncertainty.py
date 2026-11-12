"""Block bootstrap: deterministic, centred on the mean, wider when windows overlap."""
import numpy as np
import pandas as pd

from signal_origin.uncertainty import block_bootstrap_mean, paired_brier_intervals


def test_deterministic_and_contains_mean():
    d = np.random.default_rng(0).normal(0.01, 0.05, 600)
    a, b = block_bootstrap_mean(d, 63, 500, 1), block_bootstrap_mean(d, 63, 500, 1)
    assert a == b and a[1] <= a[0] <= a[2]


def test_longer_blocks_widen_range_for_persistent_errors():
    rng = np.random.default_rng(3)
    d = np.repeat(rng.normal(0, 0.05, 20), 63)        # 20 independent windows, each repeated
    w1 = np.subtract(*block_bootstrap_mean(d, 1, 800, 2)[2:0:-1])
    w63 = np.subtract(*block_bootstrap_mean(d, 63, 800, 2)[2:0:-1])
    assert w63 > 2 * w1


def test_flat50_reference_matches_definition():
    rows = pd.DataFrame({"price_date": pd.bdate_range("2020-01-01", periods=200),
                         "y": [0, 1] * 100, "p_B0": 0.5, "p_B1": 0.5})
    t = paired_brier_intervals(rows, ["B0", "B1"], "y", 21, n_boot=100)
    assert np.allclose(t.loc[t.reference.eq("FLAT50"), "brier_gain"], 0.0)
