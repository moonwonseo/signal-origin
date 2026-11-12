import json
from pathlib import Path
import subprocess
import sys
import numpy as np
import pandas as pd
import pytest

from signal_origin.cli import main
from signal_origin.io import ROOT, load_json, sha256_file, write_json
from signal_origin.runner import plan_to_folder, run_experiment, validate_to_folder
from signal_origin.spec import SYNTHETIC_STATUS, SignalOriginError


def test_complete_run_exports_auditable_synthetic_artifacts(inputs,config,tmp_path):
    folder=tmp_path/"SYNTHETIC_run"
    status=run_experiment(inputs,config,folder,allow_synthetic=True)
    assert status["evidence_status"]==SYNTHETIC_STATUS
    state=load_json(folder/"run_status.json")
    assert not state["real_data_run"] and not state["forecasting_skill_established"]
    assert state["B0_fitted"] and state["B1_fitted"] and not state["A1_implemented"]
    for path in folder.glob("*.csv"):
        table=pd.read_csv(path)
        assert table.data_kind.eq("synthetic").all()
        assert table.evidence_status.eq(SYNTHETIC_STATUS).all()
    for path in folder.glob("*.json"):
        json.loads(path.read_text(),parse_constant=lambda value:pytest.fail(f"Nonstandard JSON: {value}"))
    assert "SYNTHETIC" in (folder/"RUN_README.md").read_text()


def test_identical_inputs_reproduce_numerical_artifacts(inputs,config,tmp_path):
    folders=[tmp_path/"repeat_a",tmp_path/"repeat_b"]
    for folder in folders:
        run_experiment(inputs,config,folder,allow_synthetic=True)
    # Timestamps and absolute run paths intentionally differ in run_manifest.json.
    for name in ["predictions.csv","metrics.csv","calibration.csv","fitted_parameters.json","split_audit.json"]:
        assert sha256_file(folders[0]/name)==sha256_file(folders[1]/name)


def test_output_manifest_hashes_match_files(inputs,config,tmp_path):
    folder=tmp_path/"manifest_check"
    run_experiment(inputs,config,folder,allow_synthetic=True)
    manifest=load_json(folder/"run_manifest.json")
    for name,expected in manifest["output_sha256"].items():
        assert sha256_file(folder/name)==expected
    assert manifest["input_sha256"]==inputs.audit["input_sha256"]
    assert manifest["configuration"]==config.to_dict()


def test_nonempty_output_is_never_overwritten(inputs,config,tmp_path):
    folder=tmp_path/"do_not_overwrite";folder.mkdir();(folder/"important.txt").write_text("keep")
    with pytest.raises(SignalOriginError,match="overwrite"):
        run_experiment(inputs,config,folder,allow_synthetic=True)
    assert (folder/"important.txt").read_text()=="keep"


def test_blocked_input_creates_no_model_results(inputs,config,tmp_path):
    inputs.metadata["roll_adjustment_status"]="unverified";folder=tmp_path/"blocked"
    with pytest.raises(SignalOriginError,match="blocked"):
        run_experiment(inputs,config,folder,allow_synthetic=True)
    assert not folder.exists()


def test_plan_and_validate_do_not_fit_models(inputs,config,tmp_path):
    plan_to_folder(inputs,config,tmp_path/"plan",allow_synthetic=True)
    validate_to_folder(inputs,tmp_path/"audit")
    assert not (tmp_path/"plan"/"predictions.csv").exists()
    assert not (tmp_path/"audit"/"predictions.csv").exists()
    assert (tmp_path/"plan"/"split_audit.json").exists()


def test_cli_real_run_rejects_synthetic_without_opt_in(paths,config,tmp_path,capsys):
    config_path=tmp_path/"config.json";write_json(config_path,config.to_dict())
    args=["run","--prices",str(paths["prices"]),"--sessions",str(paths["sessions"]),"--metadata",str(paths["metadata"]),"--config",str(config_path),"--out",str(tmp_path/"not_real")]
    assert main(args)==2
    assert "allow-synthetic" in capsys.readouterr().err
    assert not (tmp_path/"not_real").exists()


def test_cli_invalid_config_fails_informatively(paths,tmp_path,capsys):
    config_path=tmp_path/"empty_config.json";write_json(config_path,{"test_start":None})
    args=["plan","--prices",str(paths["prices"]),"--sessions",str(paths["sessions"]),"--metadata",str(paths["metadata"]),"--config",str(config_path),"--allow-synthetic","--out",str(tmp_path/"bad_plan")]
    assert main(args)==2
    assert "Set test_start" in capsys.readouterr().err


def test_standalone_cli_demo_works_from_another_directory(tmp_path):
    folder=tmp_path/"SYNTHETIC_demo"
    completed=subprocess.run([sys.executable,str(ROOT/"run_baselines.py"),"demo","--out",str(folder)],cwd=tmp_path,capture_output=True,text=True,timeout=30)
    assert completed.returncode==0,completed.stderr
    assert "SYNTHETIC SOFTWARE TEST ONLY" in completed.stdout
    status=load_json(folder/"SYNTHETIC_RUN"/"run_status.json")
    assert not status["real_data_run"]


def test_config_template_intentionally_cannot_run():
    from signal_origin.spec import RunConfig
    with pytest.raises(SignalOriginError,match="test_start"):
        RunConfig.from_dict(load_json(ROOT/"config"/"run_config.template.json"))
