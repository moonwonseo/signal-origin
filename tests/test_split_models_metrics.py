import copy
import numpy as np
import pandas as pd
import pandas.testing as pdt
import pytest

from signal_origin.evaluation import calibration_table, probability_metrics, metrics_table
from signal_origin.features import build_design
from signal_origin.models import TARGET, HistoricalFrequency, fit_pair, predict_from_export
from signal_origin.spec import FEATURES, RunConfig, SignalOriginError
from signal_origin.split import make_split, nonoverlapping_origins


def test_train_outcomes_strictly_precede_test_start(inputs,config):
    split=make_split(build_design(inputs.frame),config)
    assert (split.train.label_end_date<pd.Timestamp(config.test_start)).all()
    assert split.audit["purged_training_rows"]==63
    assert split.train.session_index.max()==536
    assert len(split.train)==474 and len(split.test)==201


def test_boundary_day_outcome_is_purged(inputs,config):
    split=make_split(build_design(inputs.frame),config)
    row=split.membership.loc[537]
    assert row.label_end_date==pd.Timestamp(config.test_start)
    assert row.partition=="purged_training_outcome_at_or_after_test_start"


def test_no_random_split_and_same_order(inputs,config):
    split=make_split(build_design(inputs.frame),config)
    assert split.train.price_date.is_monotonic_increasing
    assert split.test.price_date.is_monotonic_increasing
    assert set(split.train.index).isdisjoint(split.test.index)


def test_empty_test_window_fails(inputs,config):
    altered=RunConfig(test_start=inputs.frame.price_date.iloc[-1].strftime("%Y-%m-%d"))
    with pytest.raises(SignalOriginError,match="test rows"):
        make_split(build_design(inputs.frame),altered)


def test_non_session_split_date_fails(inputs,config):
    with pytest.raises(SignalOriginError,match="must be a session"):
        make_split(build_design(inputs.frame),RunConfig(test_start="2012-04-29"))


def test_nonoverlapping_closed_windows(inputs,config):
    split=make_split(build_design(inputs.frame),config)
    picked=split.test.loc[nonoverlapping_origins(split.test)]
    for i in range(1,len(picked)):
        assert picked.price_date.iloc[i]>picked.label_end_date.iloc[i-1]
    assert len(picked)==4


def test_B0_is_training_frequency_only():
    b0=HistoricalFrequency().fit([0,1,1,0])
    assert np.array_equal(b0.predict_proba(3),[0.5]*3)


def test_B0_single_class_is_well_defined():
    assert np.array_equal(HistoricalFrequency().fit([0,0]).predict_proba(2),[0,0])


def test_B0_before_fit_fails():
    with pytest.raises(SignalOriginError,match="Fit B0"):
        HistoricalFrequency().predict_proba(2)


@pytest.mark.parametrize("y",[[],[0,2],[0,np.nan],[[0,1]]])
def test_invalid_targets_rejected(y):
    with pytest.raises(SignalOriginError,match="Targets"):
        HistoricalFrequency().fit(y)


def test_B1_fits_and_predictions_are_bounded(inputs,config):
    split=make_split(build_design(inputs.frame),config);pair=fit_pair(split.train,config);p=pair.predict(split.test)
    assert list(p.columns)==["p_B0","p_B1"]
    assert np.isfinite(p).all().all() and ((p>=0)&(p<=1)).all().all()
    assert pair.b0.n_train_==len(split.train)
    assert p.p_B0.nunique()==1


def test_scaler_is_fitted_on_training_only(inputs,config):
    split=make_split(build_design(inputs.frame),config);pair=fit_pair(split.train,config)
    assert np.allclose(pair.b1.named_steps["scale"].mean_, split.train[list(FEATURES)].mean().to_numpy())
    before=pair.b1.named_steps["scale"].mean_.copy()
    changed=split.test.copy();changed.loc[:,list(FEATURES)]*=50
    pair.predict(changed)
    assert np.array_equal(pair.b1.named_steps["scale"].mean_,before)


def test_training_fit_unchanged_by_altered_holdout_prices(inputs,config):
    design=build_design(inputs.frame);a=make_split(design,config);first=fit_pair(a.train,config)
    frame=inputs.frame.copy();mask=frame.price_date>=pd.Timestamp(config.test_start)
    frame.loc[mask,"model_price"]*=2
    frame.loc[mask,"raw_price_text"]=frame.loc[mask,"model_price"].map(str)
    b=make_split(build_design(frame),config);second=fit_pair(b.train,config)
    pdt.assert_frame_equal(a.train,b.train)
    assert first.export()==second.export()


def test_B1_rejects_single_class_instead_of_fake_fit(inputs,config):
    train=make_split(build_design(inputs.frame),config).train;train[TARGET]=0
    with pytest.raises(SignalOriginError,match="each class"):
        fit_pair(train,config)


def test_nonconvergence_is_explicit(inputs,config):
    train=make_split(build_design(inputs.frame),config).train
    tiny=RunConfig(test_start=config.test_start,max_iter=1,tolerance=1e-15)
    with pytest.raises(SignalOriginError,match="did not converge"):
        fit_pair(train,tiny)


def test_extra_label_or_weather_column_is_not_a_predictor(inputs,config):
    split=make_split(build_design(inputs.frame),config);pair=fit_pair(split.train,config)
    expected=pair.predict(split.test)
    altered=split.test.copy();altered[TARGET]=1-altered[TARGET];altered["rain_anom"]=999;altered["future_price_63"]=999
    pdt.assert_frame_equal(expected,pair.predict(altered))


def test_exported_parameters_reproduce_sklearn(inputs,config):
    split=make_split(build_design(inputs.frame),config);pair=fit_pair(split.train,config)
    assert np.allclose(predict_from_export(split.test,pair.export()),pair.predict(split.test).p_B1,rtol=1e-12,atol=1e-12)


def test_bad_export_feature_order_fails(inputs,config):
    split=make_split(build_design(inputs.frame),config);pair=fit_pair(split.train,config);export=pair.export();export["feature_order"]=list(reversed(FEATURES))
    with pytest.raises(SignalOriginError,match="feature order"):
        predict_from_export(split.test,export)


def test_Brier_binary_scale_and_reference_values():
    assert probability_metrics([0,1],[0.5,0.5])["brier_score"]==0.25
    assert probability_metrics([0,1],[0,1])["brier_score"]==0
    assert probability_metrics([0,1],[1,0])["brier_score"]==1
    assert probability_metrics([0,1,1,0],[0.25]*4)["brier_score"]==0.3125


def test_one_class_test_metrics_do_not_crash():
    metrics=probability_metrics([0,0,0],[0.1,0.2,0.3])
    assert metrics["roc_auc"] is None
    assert metrics["roc_auc_status"]=="undefined_single_class"
    assert np.isfinite(metrics["brier_score"]) and np.isfinite(metrics["log_loss"])


@pytest.mark.parametrize("p",[[-0.1,0.5],[0.5,1.1],[np.nan,0.5],[0.5],[np.inf,0]])
def test_invalid_probabilities_rejected(p):
    with pytest.raises(SignalOriginError,match="Probabilities"):
        probability_metrics([0,1],p)


def test_calibration_bin_endpoints_and_empty_bins():
    table=calibration_table([0,0,1,1],[0,0.2,0.8,1.0],5)
    assert table.n_forecasts.sum()==4
    assert table.n_forecasts.tolist()==[1,1,0,0,2]
    assert pd.isna(table.loc[2,"observed_event_frequency"])
    assert table.loc[4,"upper_bound_inclusive"]


def test_positive_Brier_difference_means_improvement():
    table=metrics_table([0,1],pd.DataFrame({"p_B0":[0.5,0.5],"p_B1":[0,1]}),"synthetic_reference")
    assert table.loc[0,"brier_improvement_vs_B0"]==0
    assert table.loc[1,"brier_improvement_vs_B0"]==0.25


@pytest.mark.parametrize("updates",[{"test_start":None},{"C":0},{"C":float('nan')},{"min_train_rows":True},{"calibration_bins":1},{"seed":-1},{"test_end":"2000-01-01"},{"horizon":21}])
def test_invalid_config_rejected(config,updates):
    values=config.to_dict();values.update(updates)
    with pytest.raises(SignalOriginError):
        RunConfig.from_dict(values)
