"""Portable V4 orchestration over explicit, local inputs; no archive dependency."""
from __future__ import annotations

import argparse
import importlib.metadata
from pathlib import Path
import sys

import numpy as np
import pandas as pd

from . import freight as f
from .features import feature_frame
from .io import Inputs, load_inputs, require_model_ready, write_json
from .runner import fresh_directory
from .spec import RunConfig, SignalOriginError, SYNTHETIC_STATUS, HISTORICAL_STATUS


def prepare_base(frame: pd.DataFrame, weather: pd.DataFrame) -> pd.DataFrame:
    """Exact t-4 weather join. Supplied anomalies must be audited separately."""
    columns = ["weather_date_utc", "rain_anom_z", "temp_anom_z", "dry_spell_max_30d"]
    if not set(columns).issubset(weather):
        raise SignalOriginError(f"Weather features require {columns}.")
    w = weather[columns].copy()
    w["weather_date_utc"] = pd.to_datetime(w.weather_date_utc, errors="raise")
    dates = w.weather_date_utc
    if dates.isna().any() or dates.duplicated().any() or not dates.is_monotonic_increasing:
        raise SignalOriginError("Weather dates must be present, unique and sorted.")
    if not dates.eq(dates.dt.normalize()).all() or dates.dt.tz is not None:
        raise SignalOriginError("Weather dates must be naive UTC calendar-day labels.")
    for name in columns[1:]:
        w[name] = pd.to_numeric(w[name], errors="raise")
        if np.isinf(w[name]).any():
            raise SignalOriginError("Infinite weather features are invalid.")
    dry = w.dry_spell_max_30d.dropna()
    if not (dry.between(0, 30) & dry.eq(np.floor(dry))).all():
        raise SignalOriginError("Dry-spell duration must be an integer from 0 through 30.")
    base = frame[["price_date", "session_index", "close_us_cents_per_lb"]].copy()
    base = base.join(feature_frame(frame))
    base["weather_observation_date"] = base.price_date - pd.Timedelta(days=4)
    base = base.merge(w, left_on="weather_observation_date", right_on="weather_date_utc",
                      how="left", sort=False, validate="one_to_one")
    base.index = frame.index
    base["features_ready"] = np.isfinite(base[list(f.A1_FEATURES)].to_numpy(dtype=float)).all(axis=1)
    return base


def annual_folds(design: pd.DataFrame, horizon: int, years):
    """Each annual fit sees only complete outcomes ending before its first session."""
    for year in years:
        dates = design.loc[design.price_date.dt.year.eq(year), "price_date"]
        if dates.empty:
            raise SignalOriginError(f"No supplied sessions for fold {year}.")
        cfg = RunConfig(test_start=dates.min().strftime("%Y-%m-%d"),
                        test_end=dates.max().strftime("%Y-%m-%d"))
        split = f.make_split(design, cfg)
        split.audit.update(horizon_exchange_sessions=horizon, fold_year=year,
                           split_kind="annual_expanding_fit_fixed_within_year",
                           same_sample_all_models=True,
                           warning=f"Overlapping {horizon}-session outcomes are dependent; no IID significance claims.")
        split.audit["test_rows_excluded_incomplete_future_window"] = split.audit.pop("test_rows_excluded_missing_endpoint")
        yield year, cfg, split


def analyze(inputs: Inputs, weather: pd.DataFrame, monthly: pd.DataFrame,
            years=(2022, 2023, 2024, 2025, 2026), *, allow_synthetic=False):
    """Run all seven models on matched rows for both policies and horizons."""
    require_model_ready(inputs, allow_synthetic=allow_synthetic)
    years = tuple(years)
    if not years or any(type(y) is not int for y in years) or list(years) != sorted(set(years)):
        raise SignalOriginError("Fold years must be distinct integers in increasing order.")
    base = prepare_base(inputs.frame, weather)
    predictions, metrics, annual, calibration, audits, designs = [], [], [], [], [], {}
    parameters = {}
    for policy, lag in f.POLICIES.items():
        for horizon in (63, 21):
            design = f.build_design(base, inputs.frame, monthly, horizon, lag)
            designs[f"{policy}_h{horizon}"] = design
            fold_predictions = []
            for year, config, split in annual_folds(design, horizon, years):
                pred, params = f.fit_models(split.train, split.test, config)
                columns = ["price_date", "session_index", f.Y, "label_end_date", "first_cross_date",
                           "weather_observation_date", "freight_observation_month", "freight_period_end",
                           "assumed_freight_available_date"]
                display_features = sorted({c for cols in f.MODEL_FEATURES.values() for c in cols})
                rows = split.test[columns + display_features].join(pred).assign(
                    policy=policy, horizon=horizon, fold_year=year)
                fold_predictions.append(rows)
                annual.append(f.score(rows, "annual_fold").assign(policy=policy, horizon=horizon, fold_year=year))
                audits.append({"policy": policy, **split.audit})
                parameters[f"{policy}/h{horizon}/{year}"] = params
            rows = pd.concat(fold_predictions, ignore_index=True).sort_values("price_date")
            predictions.append(rows)
            scopes = {"all_available_dates": rows,
                      "recent_dates_from_2024": rows.loc[rows.price_date >= pd.Timestamp("2024-01-01")],
                      "earliest_disjoint_windows_diagnostic": rows.loc[f.nonoverlapping_origins(rows)]}
            for scope, subset in scopes.items():
                if subset.empty:
                    continue
                metrics.append(f.score(subset, scope).assign(policy=policy, horizon=horizon))
                for model in f.MODELS:
                    calibration.append(f.calibration_table(subset[f.Y], subset["p_" + model]).assign(
                        policy=policy, horizon=horizon, scope=scope, model=model))
    kind = inputs.metadata["data_kind"]
    status = SYNTHETIC_STATUS if kind == "synthetic" else HISTORICAL_STATUS
    tables = {"predictions": pd.concat(predictions, ignore_index=True),
              "metrics": pd.concat(metrics, ignore_index=True),
              "annual": pd.concat(annual, ignore_index=True),
              "calibration": pd.concat(calibration, ignore_index=True)}
    for table in tables.values():
        table["data_kind"] = kind
        table["evidence_status"] = status
    return {**tables, "audits": audits, "parameters": parameters, "designs": designs,
            "meta": {"data_kind": kind, "evidence_status": status, "fold_years": list(years),
                     "forecasting_skill_established": False, "original_archive_reproduction": False,
                     "dependencies": {n: importlib.metadata.version(n) for n in
                                      ("numpy", "pandas", "scipy", "scikit-learn")}}}


def save_analysis(result, out: Path):
    fresh_directory(out)
    write_json(out / "run_receipt.json", {**result["meta"], "completed": False})
    for name in ("predictions", "metrics", "annual", "calibration"):
        result[name].to_csv(out / f"{name}.csv", index=False, float_format="%.17g")
    write_json(out / "fold_audits.json", result["audits"])
    write_json(out / "fitted_parameters.json", result["parameters"])
    write_json(out / "run_receipt.json", {**result["meta"], "completed": True})


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline V4 research; no live forecasting or downloads.")
    subs = parser.add_subparsers(dest="command", required=True)
    synthetic = subs.add_parser("synthetic", help="Fit all seven models on artificial data only.")
    synthetic.add_argument("--out", type=Path, required=True)
    run = subs.add_parser("run", help="Use independently obtained and audited local inputs.")
    for name in ("prices", "sessions", "metadata", "weather-features", "freight", "out"):
        run.add_argument("--" + name, type=Path, required=True)
    run.add_argument("--years", type=int, nargs="+", required=True)
    run.add_argument("--acknowledge-exploratory", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.out.exists() and any(args.out.iterdir()):
            raise SignalOriginError("Use a new or empty output directory.")
        if args.command == "synthetic":
            from .synthetic_v4 import make_inputs
            inputs, weather, monthly = make_inputs()
            result = analyze(inputs, weather, monthly, allow_synthetic=True)
        else:
            if not args.acknowledge_exploratory:
                raise SignalOriginError("Explicit --acknowledge-exploratory is required.")
            inputs = load_inputs(args.prices, args.sessions, args.metadata)
            weather = pd.read_csv(args.weather_features)
            monthly = pd.read_csv(args.freight)
            result = analyze(inputs, weather, monthly, args.years)
            result["meta"]["input_sha256"] = inputs.audit["input_sha256"]
            from .io import sha256_file
            result["meta"]["context_sha256"] = {"weather_features": sha256_file(args.weather_features),
                                                "freight": sha256_file(args.freight)}
        save_analysis(result, args.out)
        print(f"Completed {result['meta']['evidence_status']}: {args.out}")
        return 0
    except (SignalOriginError, ValueError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
