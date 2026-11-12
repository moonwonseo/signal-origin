"""Check the distributable HTML against its synthetic data contract."""
import hashlib
import json
from pathlib import Path
import re

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def data():
    html = (ROOT / "demo/index.html").read_text()
    encoded = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)[1]
    return json.loads(encoded)


def test_public_demo_is_explicitly_synthetic_with_integrity_hash(data):
    assert data["meta"]["data_kind"] == "synthetic"
    assert data["meta"]["experiment"] == "SYNTHETIC_SOFTWARE_TEST_ONLY"
    assert not data["meta"]["original_archive_reproduction"]
    copied = json.loads(json.dumps(data))
    expected = copied["meta"].pop("payload_sha256")
    raw = json.dumps(copied, sort_keys=True, separators=(",", ":"), allow_nan=False)
    assert hashlib.sha256(raw.encode()).hexdigest() == expected


def test_demo_outcomes_match_artificial_paths_and_complete_windows(data):
    for row in data["rows"]:
        i, h = row["session_index"], row["horizon"]
        path = data["prices"][i + 1:i + h + 1]
        assert len(path) == h
        threshold = data["prices"][i][1] * 1.1
        crossing = next((date for date, value in path if value >= threshold), None)
        assert row["target_spike"] == int(crossing is not None)
        assert row["first_cross_date"] == crossing
        assert row["label_end_date"] == path[-1][0]


def test_all_demo_controls_have_matching_metrics(data):
    for horizon in (21, 63):
        for policy in ("delayed_180d_primary", "fast_45d_revised_sensitivity"):
            for scope in ("all_available_dates", "recent_dates_from_2024"):
                rows = [r for r in data["rows"] if r["horizon"] == horizon and r["policy"] == policy
                        and (scope == "all_available_dates" or r["price_date"] >= "2024-01-01")]
                metrics = [m for m in data["metrics"] if m["horizon"] == horizon and m["policy"] == policy and m["scope"] == scope]
                assert len(metrics) == 7 and rows
                for metric in metrics:
                    loss = np.mean([(r["p_" + metric["model"]] - r["target_spike"]) ** 2 for r in rows])
                    assert metric["brier_score"] == pytest.approx(loss, abs=1e-14)


def test_demo_has_no_external_assets_or_network_calls():
    html = (ROOT / "demo/index.html").read_text()
    assert 'connect-src \'none\'' in html
    assert not re.search(r'(?:src|href)=["\']https?://|\bfetch\s*\(|XMLHttpRequest|WebSocket', html)
    assert "__PAYLOAD__" not in html
