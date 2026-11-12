"""V5 end to end on synthetic data, plus the sign-off and input gates for historical runs."""
import json

import pandas as pd
import pytest

from signal_origin import v5
from signal_origin.synthetic_v5 import make_inputs


@pytest.fixture(scope="module")
def quick(tmp_path_factory):
    out = tmp_path_factory.mktemp("v5") / "run"
    assert v5.main(["synthetic", "--quick", "--out", str(out)]) == 0
    return out


def test_outputs_and_matched_samples(quick):
    m = pd.read_csv(quick / "metrics.csv")
    assert set(m.model) == {"B0", "B1", "A1", "A3"}
    assert set(m.variant) == {"grid", "liquidity_sensitivity"}
    same = m.groupby(["variant", "threshold_pct", "horizon", "scope"]).n_forecasts.nunique()
    assert (same == 1).all()                                   # every model scored on the same rows
    assert (m.loc[m.model.eq("B0"), "brier_skill_vs_B0"].abs() < 1e-12).all()
    i = pd.read_csv(quick / "intervals.csv")
    assert set(i.reference) == {"B0", "FLAT50"} and (i.range_low_95 <= i.range_high_95).all()
    r = json.loads((quick / "run_receipt.json").read_text())
    assert r["completed"] and r["evidence_status"] == "SYNTHETIC_SOFTWARE_TEST_ONLY"


def test_training_never_sees_test_outcomes(quick):
    audits = json.loads((quick / "fold_audits.json").read_text())
    for a in audits:
        assert a["latest_training_outcome_date"] < a["test_origin_start"]


def _historical(monkeypatch, tmp_path, status, signers):
    inputs, single, long, weights, mask = make_inputs()
    inputs.metadata.update(data_kind="historical", calendar_verified=True,
                           roll_adjustment_status="documented_return_compatible")
    monkeypatch.setattr(v5, "load_inputs", lambda *a: inputs)
    spec = json.loads(open("configs/v5_spec.json").read())
    spec.update(status=status, signed_off_by=signers, fold_years=[2025, 2026], thresholds_pct=[10],
                horizons_sessions=[21], models=["B0", "B1", "A1"])
    sp = tmp_path / "spec.json"; sp.write_text(json.dumps(spec))
    single.to_csv(tmp_path / "w.csv", index=False)
    base = ["run", "--spec", str(sp), "--prices", "x", "--sessions", "x", "--metadata", "x",
            "--weather-features", str(tmp_path / "w.csv"), "--acknowledge-exploratory"]
    return base


def test_unsigned_spec_blocks_fitting_but_allows_dry_run(monkeypatch, tmp_path):
    base = _historical(monkeypatch, tmp_path, "DRAFT", [])
    assert v5.main(base + ["--out", str(tmp_path / "a")]) == 2
    assert v5.main(base + ["--dry-run", "--out", str(tmp_path / "b")]) == 0
    assert not (tmp_path / "b" / "metrics.csv").exists()


def test_signed_spec_allows_fitting(monkeypatch, tmp_path):
    base = _historical(monkeypatch, tmp_path, "SIGNED_OFF", ["Celine", "Moonwon"])
    assert v5.main(base + ["--out", str(tmp_path / "c")]) == 0
    assert (tmp_path / "c" / "metrics.csv").exists()
