import json
import numpy as np
import pandas as pd
import pytest
from signal_origin.io import load_inputs, load_json, require_model_ready, write_json
from signal_origin.spec import SignalOriginError


def update_meta(paths, **updates):
    meta = load_json(paths["metadata"]); meta.update(updates); write_json(paths["metadata"], meta)


def test_valid_input_counts_and_provenance(inputs):
    assert inputs.audit["source_rows"] == 900
    assert inputs.audit["unusable_prices"] == 0
    assert all(len(x) == 64 for x in inputs.audit["input_sha256"].values())
    assert inputs.evidence_status == "SYNTHETIC_SOFTWARE_TEST_ONLY"


def test_duplicate_date_rejected(paths):
    p = pd.read_csv(paths["prices"]); p.loc[1,"price_date"] = p.loc[0,"price_date"]; p.to_csv(paths["prices"],index=False)
    with pytest.raises(SignalOriginError, match="Duplicate dates"):
        load_inputs(**paths)


def test_duplicate_header_rejected(paths):
    text = paths["prices"].read_text().replace("quality_status", "price_date", 1); paths["prices"].write_text(text)
    with pytest.raises(SignalOriginError, match="Duplicate column"):
        load_inputs(**paths)


@pytest.mark.parametrize("bad", ["1/2/2020", "2020-1-2", "2020-01-02T15:00:00Z", "2020-02-30", ""])
def test_bad_date_rejected(paths,bad):
    p=pd.read_csv(paths["prices"]); p.loc[1,"price_date"]=bad; p.to_csv(paths["prices"],index=False)
    with pytest.raises(SignalOriginError, match="date"):
        load_inputs(**paths)


@pytest.mark.parametrize("bad", ["0", "-1", "inf", "NaN", "garbage", "1,200", "1e1000"])
def test_nonpositive_or_invalid_price_rejected(paths,bad):
    p=pd.read_csv(paths["prices"],dtype=str); p.loc[100,"close_us_cents_per_lb"]=bad; p.to_csv(paths["prices"],index=False)
    with pytest.raises(SignalOriginError, match="[Pp]rice"):
        load_inputs(**paths)


def test_blank_price_preserved_as_missing(paths):
    p=pd.read_csv(paths["prices"],dtype=str); p.loc[100,"close_us_cents_per_lb"]=""; p.to_csv(paths["prices"],index=False)
    result=load_inputs(**paths)
    assert len(result.frame)==900 and np.isnan(result.frame.loc[100,"model_price"])
    assert result.audit["unusable_prices"]==1


def test_omitted_session_reinserted_not_forward_filled(paths):
    p=pd.read_csv(paths["prices"]); p.drop(index=100).to_csv(paths["prices"],index=False)
    result=load_inputs(**paths)
    assert result.audit["inserted_missing_session_rows"]==1
    assert len(result.frame)==900 and np.isnan(result.frame.loc[100,"model_price"])


def test_review_price_quarantined_but_raw_preserved(paths):
    p=pd.read_csv(paths["prices"]); p.loc[100,"quality_status"]="review"; value=p.loc[100,"close_us_cents_per_lb"];p.to_csv(paths["prices"],index=False)
    result=load_inputs(**paths)
    assert result.frame.loc[100,"close_us_cents_per_lb"]==value
    assert np.isnan(result.frame.loc[100,"model_price"])


def test_unknown_quality_rejected(paths):
    p=pd.read_csv(paths["prices"]); p.loc[1,"quality_status"]="probably good";p.to_csv(paths["prices"],index=False)
    with pytest.raises(SignalOriginError,match="quality_status"):
        load_inputs(**paths)


def test_two_column_minimum_supported(paths):
    p=pd.read_csv(paths["prices"]).drop(columns="quality_status");p.to_csv(paths["prices"],index=False)
    result=load_inputs(**paths)
    assert result.audit["usable_prices"]==900
    assert any("No row quality_status" in s for s in result.audit["warnings"])


def test_extra_feature_columns_never_enter_contract(paths):
    p=pd.read_csv(paths["prices"]);p["future_cheat"]=123;p.to_csv(paths["prices"],index=False)
    result=load_inputs(**paths)
    assert "future_cheat" in result.audit["extra_price_columns_ignored_by_model"]


def test_unsorted_rows_are_sorted_and_reported(paths):
    p=pd.read_csv(paths["prices"]);p.iloc[::-1].to_csv(paths["prices"],index=False)
    result=load_inputs(**paths)
    assert result.frame.price_date.is_monotonic_increasing
    assert any("sorted" in s for s in result.audit["warnings"])


def test_price_outside_calendar_rejected(paths):
    p=pd.read_csv(paths["sessions"]);p.drop(index=10).to_csv(paths["sessions"],index=False)
    with pytest.raises(SignalOriginError,match="outside"):
        load_inputs(**paths)


def test_calendar_edge_mismatch_rejected(paths):
    p=pd.read_csv(paths["prices"]);p.iloc[1:].to_csv(paths["prices"],index=False)
    with pytest.raises(SignalOriginError,match="first and last"):
        load_inputs(**paths)


def test_sparse_monthly_calendar_rejected(paths):
    p=pd.read_csv(paths["prices"]).iloc[:12].copy()
    dates=pd.date_range("2015-01-01",periods=12,freq="MS").strftime("%Y-%m-%d")
    p["price_date"]=dates;p.to_csv(paths["prices"],index=False)
    pd.DataFrame({"session_date":dates}).to_csv(paths["sessions"],index=False)
    with pytest.raises(SignalOriginError,match="too sparse"):
        load_inputs(**paths)


@pytest.mark.parametrize("key,value",[("price_units","usd_per_kg"),("frequency","monthly"),("instrument","FRED_OTHER_MILDS"),("calendar_verified","true"),("unexpected",1)])
def test_bad_metadata_rejected(paths,key,value):
    update_meta(paths,**{key:value})
    with pytest.raises(SignalOriginError,match="Metadata"):
        load_inputs(**paths)


def test_naive_retrieval_timestamp_rejected(paths):
    update_meta(paths,retrieved_at_utc="2026-10-12T12:00:00.00")
    with pytest.raises(SignalOriginError,match="UTC"):
        load_inputs(**paths)


def test_synthetic_requires_explicit_opt_in(inputs):
    with pytest.raises(SignalOriginError,match="allow-synthetic"):
        require_model_ready(inputs)
    require_model_ready(inputs,allow_synthetic=True)


@pytest.mark.parametrize("key,value",[("roll_adjustment_status","unverified"),("calendar_verified",False)])
def test_unverified_source_can_be_audited_but_not_modeled(paths,key,value):
    update_meta(paths,**{key:value})
    result=load_inputs(**paths)
    assert result.audit["model_readiness_blockers"]
    with pytest.raises(SignalOriginError,match="blocked"):
        require_model_ready(result,allow_synthetic=True)


def test_historical_metadata_requires_actual_instrument_and_http_source(paths):
    update_meta(paths,data_kind="historical",point_in_time_status="unverified_retrospective")
    with pytest.raises(SignalOriginError,match="Metadata"):
        load_inputs(**paths)


def test_header_only_template_is_not_data(paths):
    paths["prices"].write_text("price_date,close_us_cents_per_lb\n")
    with pytest.raises(SignalOriginError,match="no rows"):
        load_inputs(**paths)


def test_duplicate_json_key_rejected(paths):
    paths["metadata"].write_text('{"a": 1, "a": 2}')
    with pytest.raises(SignalOriginError,match="Duplicate JSON"):
        load_json(paths["metadata"])


def test_nonstandard_nan_json_rejected(paths):
    paths["metadata"].write_text('{"a": NaN}')
    with pytest.raises(SignalOriginError,match="Non-standard"):
        load_json(paths["metadata"])
