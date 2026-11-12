"""End-to-end V4 safeguards using artificial inputs exclusively."""
import numpy as np
import pandas as pd
import pytest

from signal_origin import freight as f
from signal_origin.experiment import analyze, annual_folds, prepare_base, save_analysis, main
from signal_origin.spec import SignalOriginError, SYNTHETIC_STATUS
from signal_origin.synthetic_v4 import make_inputs


@pytest.fixture(scope="module")
def v4():
    inputs, weather, monthly = make_inputs()
    return analyze(inputs, weather, monthly, years=(2024,), allow_synthetic=True)


def test_matched_forecasts_have_complete_matured_windows_and_correct_timing(v4):
    assert len(v4["audits"]) == 4
    for audit in v4["audits"]:
        assert audit["latest_training_outcome_date"] < audit["test_start_requested"]
        assert audit["same_sample_all_models"]
    rows = v4["predictions"]
    assert not rows.duplicated(["policy", "horizon", "price_date"]).any()
    assert (rows.weather_observation_date == rows.price_date - pd.Timedelta(days=4)).all()
    assert (rows.assumed_freight_available_date < rows.price_date).all()
    assert rows[f.Y].notna().all() and rows.label_end_date.notna().all()
    assert rows[["p_" + m for m in f.MODELS]].apply(lambda x: x.between(0, 1)).all().all()


def test_scores_reconstruct_from_the_same_model_sample(v4):
    for row in v4["metrics"].itertuples():
        if row.scope != "all_available_dates":
            continue
        p = v4["predictions"].query("policy == @row.policy and horizon == @row.horizon")
        assert len(p) == row.n_forecasts
        expected = np.mean((p["p_" + row.model] - p[f.Y].astype(float)) ** 2)
        assert row.brier_score == pytest.approx(expected, abs=1e-14)


def test_synthetic_status_propagates_to_every_export(v4, tmp_path):
    save_analysis(v4, tmp_path / "output")
    for name in ("predictions", "metrics", "annual", "calibration"):
        assert v4[name].data_kind.eq("synthetic").all()
        assert v4[name].evidence_status.eq(SYNTHETIC_STATUS).all()
    assert not v4["meta"]["forecasting_skill_established"]
    assert not v4["meta"]["original_archive_reproduction"]


def test_synthetic_requires_explicit_opt_in():
    inputs, weather, monthly = make_inputs()
    with pytest.raises(SignalOriginError, match="allow-synthetic"):
        analyze(inputs, weather, monthly, years=(2024,))


def test_future_feature_and_label_changes_leave_earlier_training_unchanged():
    inputs, weather, monthly = make_inputs()
    design = f.build_design(prepare_base(inputs.frame, weather), inputs.frame, monthly, 63, 180)
    _, config, before = next(annual_folds(design, 63, (2024,)))
    changed = design.copy(deep=True)
    mask = changed.price_date >= pd.Timestamp(config.test_start)
    changed.loc[mask, f.Y] = 1 - changed.loc[mask, f.Y]
    changed.loc[mask, "rain_anom_z"] = 1000
    _, _, after = next(annual_folds(changed, 63, (2024,)))
    pd.testing.assert_frame_equal(before.train, after.train)


@pytest.mark.parametrize("bad", ["duplicate", "unsorted", "infinite", "duration"])
def test_invalid_weather_features_are_rejected(bad):
    inputs, weather, _ = make_inputs()
    if bad == "duplicate":
        weather.loc[1, "weather_date_utc"] = weather.loc[0, "weather_date_utc"]
    elif bad == "unsorted":
        weather = weather.iloc[::-1]
    elif bad == "infinite":
        weather.loc[0, "temp_anom_z"] = np.inf
    else:
        weather.loc[0, "dry_spell_max_30d"] = 31
    with pytest.raises(SignalOriginError):
        prepare_base(inputs.frame, weather)


def test_cli_requires_acknowledgment_before_reading_private_inputs(tmp_path, capsys):
    args = ["run", "--years", "2024"]
    for name in ("prices", "sessions", "metadata", "weather-features", "freight"):
        args += ["--" + name, "missing.csv"]
    args += ["--out", str(tmp_path / "blocked")]
    assert main(args) == 2
    assert "acknowledge-exploratory" in capsys.readouterr().err
    assert not (tmp_path / "blocked").exists()
