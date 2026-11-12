"""Auditable execution: no model results are written unless fitting succeeds."""
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
from pathlib import Path
import platform
import sys

import pandas as pd

from . import __version__
from .evaluation import calibration_table, metrics_table
from .features import build_design
from .io import Inputs, ROOT, require_model_ready, sha256_file, write_json
from .models import TARGET, fit_pair
from .spec import FEATURES, HORIZON, THRESHOLD, RunConfig, SYNTHETIC_STATUS, SignalOriginError
from .split import make_split, nonoverlapping_origins


def fresh_directory(folder: Path) -> None:
    if folder.exists() and (not folder.is_dir() or any(folder.iterdir())):
        raise SignalOriginError(f"Output path must be new or empty; refusing to overwrite evidence: {folder}")
    folder.mkdir(parents=True, exist_ok=True)


def tag_table(frame: pd.DataFrame, inputs: Inputs) -> pd.DataFrame:
    result = frame.copy()
    result.insert(0, "evidence_status", inputs.evidence_status)
    result.insert(0, "data_kind", inputs.metadata["data_kind"])
    return result


def export_table(path: Path, frame: pd.DataFrame, inputs: Inputs) -> None:
    tag_table(frame, inputs).to_csv(path, index=False, date_format="%Y-%m-%d", float_format="%.17g")


def environment_info() -> dict:
    names = ["numpy", "pandas", "scipy", "scikit-learn", "jsonschema"]
    return {"python": sys.version.split()[0], "platform": platform.platform(),
            "packages": {name: version(name) for name in names}}


def code_hashes() -> dict[str, str]:
    files = sorted((ROOT / "signal_origin").glob("*.py")) + sorted((ROOT / "signal_origin/schema").glob("*.json"))
    return {str(p.relative_to(ROOT)): sha256_file(p) for p in files}


def export_manifest(folder: Path, inputs: Inputs, config: RunConfig | None, kind: str) -> None:
    output_hashes = {p.name: sha256_file(p) for p in sorted(folder.iterdir()) if p.is_file() and p.name != "run_manifest.json"}
    manifest = {
        "package_version": __version__, "execution_kind": kind,
        "data_kind": inputs.metadata["data_kind"], "evidence_status": inputs.evidence_status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": environment_info(),
        "input_files": {k: str(v.resolve()) for k, v in inputs.paths.items()},
        "input_sha256": inputs.audit["input_sha256"], "source_code_sha256": code_hashes(),
        "configuration": config.to_dict() if config else None, "output_sha256": output_hashes,
        "forecasting_skill_established": False,
        "note": "A retrospective run is not independent validation or procurement profit evidence; synthetic metrics are only software-test artifacts.",
    }
    write_json(folder / "run_manifest.json", manifest)


def validate_to_folder(inputs: Inputs, folder: Path) -> dict:
    fresh_directory(folder)
    write_json(folder / "input_audit.json", inputs.audit)
    write_json(folder / "input_metadata.json", inputs.metadata)
    cols = ["price_date", "session_index", "raw_price_text", "close_us_cents_per_lb", "quality_status", "price_usable", "model_price"]
    export_table(folder / "calendar_aligned_prices.csv", inputs.frame[cols], inputs)
    export_manifest(folder, inputs, None, "input_validation_no_model_fit")
    return inputs.audit


def plan_to_folder(inputs: Inputs, config: RunConfig, folder: Path, allow_synthetic: bool = False) -> dict:
    require_model_ready(inputs, allow_synthetic)
    design = build_design(inputs.frame)
    split = make_split(design, config)
    fresh_directory(folder)
    write_json(folder / "split_audit.json", {"data_kind": inputs.metadata["data_kind"], "evidence_status": inputs.evidence_status, **split.audit})
    export_table(folder / "split_membership.csv", split.membership, inputs)
    write_json(folder / "frozen_config.json", config.to_dict())
    export_manifest(folder, inputs, config, "split_planning_no_model_fit")
    return split.audit


def run_experiment(inputs: Inputs, config: RunConfig, folder: Path, allow_synthetic: bool = False) -> dict:
    # Check before expensive fitting, but do not create artifacts until success.
    if folder.exists() and (not folder.is_dir() or any(folder.iterdir())):
        raise SignalOriginError(f"Refusing to overwrite nonempty output path: {folder}")
    require_model_ready(inputs, allow_synthetic)
    design = build_design(inputs.frame)
    split = make_split(design, config)
    models = fit_pair(split.train, config)
    probabilities = models.predict(split.test)
    predictions = split.test[["price_date", "session_index", "label_end_date", TARGET]].join(probabilities)
    primary = metrics_table(split.test[TARGET], probabilities, "all_eligible_test_origins")
    selected = nonoverlapping_origins(split.test)
    diagnostics = metrics_table(split.test.loc[selected, TARGET], probabilities.loc[selected], "strictly_nonoverlapping_target_windows_diagnostic")
    calibration = pd.concat([
        calibration_table(split.test[TARGET], probabilities[f"p_{name}"], config.calibration_bins).assign(model=name)
        for name in ("B0", "B1")
    ], ignore_index=True)
    exported_model = models.export()
    status = inputs.evidence_status
    exported_model.update({"data_kind": inputs.metadata["data_kind"], "evidence_status": status})
    coefficients = pd.DataFrame({"feature": list(FEATURES),
        "standardized_coefficient": exported_model["B1_coefficients_standardized"],
        "training_mean": exported_model["scaler_mean"], "training_scale": exported_model["scaler_scale"]})
    fresh_directory(folder)
    tables = {
        "features_and_labels_NOT_INFERENCE_INPUT.csv": design,
        "split_membership.csv": split.membership,
        "predictions.csv": predictions,
        "metrics.csv": primary,
        "metrics_nonoverlapping_diagnostic.csv": diagnostics,
        "nonoverlapping_forecast_dates.csv": predictions.loc[selected],
        "calibration.csv": calibration,
        "coefficients.csv": coefficients,
    }
    for name, frame in tables.items():
        export_table(folder / name, frame, inputs)
    write_json(folder / "input_audit.json", inputs.audit)
    write_json(folder / "input_metadata.json", inputs.metadata)
    write_json(folder / "frozen_config.json", config.to_dict())
    write_json(folder / "split_audit.json", {"data_kind": inputs.metadata["data_kind"], "evidence_status": status, **split.audit})
    write_json(folder / "fitted_parameters.json", exported_model)
    b0 = float(primary.loc[primary["model"].eq("B0"), "brier_score"].iloc[0])
    b1 = float(primary.loc[primary["model"].eq("B1"), "brier_score"].iloc[0])
    limitations = [
        "No A1 or weather feature has been implemented or evaluated.",
        "No hyperparameter search, classification-threshold tuning, or post-hoc probability recalibration was performed.",
        "B0 and B1 share exactly the same training and test origins.",
        "Each training endpoint strictly predates test_start; models are then fixed throughout the holdout.",
        "Target windows overlap. Calibration and scores are descriptive; no independent-event confidence intervals are supplied.",
        "The nonoverlapping-window diagnostic is not proof of statistical independence and may be very small.",
        "The selected continuous-series proxy is not a supplier quote, purchasing-cost model, or tradable futures P&L.",
        "Passing user-supplied provenance gates does not independently certify source construction or point-in-time availability.",
    ]
    if status == SYNTHETIC_STATUS:
        headline = "SYNTHETIC SOFTWARE CHECK — NOT COFFEE FORECASTING EVIDENCE"
        interpretation = "Both baselines were exercised on artificial data. Their scores have no interpretation as real market performance."
    else:
        headline = "RETROSPECTIVE BASELINE EXPERIMENT — NOT LIVE VALIDATION"
        direction = "lower" if b1 < b0 else "higher" if b1 > b0 else "equal"
        interpretation = f"On this frozen holdout, B1's Brier score was {direction} than B0's. This single comparison establishes neither robust forecasting skill nor a weather advantage."
    lines = [f"# {headline}", "", f"Evidence status: `{status}`", "",
             f"Target: endpoint price at {HORIZON} supplied exchange sessions >= {THRESHOLD} times origin price.", "",
             f"Training origins: {len(split.train)}. Test origins: {len(split.test)}. Purged training origins: {split.audit['purged_training_rows']}.", "",
             interpretation, "", "Detailed numerical outputs are in metrics.csv; do not detach them from their evidence-status labels.", "",
             "## Limitations and interpretation rules", ""] + ["- " + x for x in limitations]
    (folder / "RUN_README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_json(folder / "run_status.json", {
        "data_kind": inputs.metadata["data_kind"], "evidence_status": status,
        "B0_fitted": True, "B1_fitted": True, "A1_implemented": False,
        "real_data_run": inputs.metadata["data_kind"] == "historical",
        "n_train": len(split.train), "n_test": len(split.test),
        "forecasting_skill_established": False, "limitations": limitations,
    })
    export_manifest(folder, inputs, config, "B0_B1_research_run")
    return {"evidence_status": status, "n_train": len(split.train), "n_test": len(split.test), "output": str(folder.resolve())}
