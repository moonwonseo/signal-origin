"""V5: better weather (six regions, crop stages), longer history, threshold/horizon grid.

Additive to V4: no V4 module is modified, and V4 commands and outputs are unchanged.
Reuses V4's price features, chronological split with matured-label purging, B0/B1 fitting and
metrics. New pieces: v5_labels (threshold parameter, liquidity mask), crop_weather (model A3),
uncertainty (block-bootstrap ranges, always-50% reference).

    python -m signal_origin.v5 synthetic --out runs/v5-synthetic
    python -m signal_origin.v5 run --spec configs/v5_spec.json --prices ... --sessions ... \
        --metadata ... --weather-features ... --region-weather ... [--liquidity ...] \
        --acknowledge-exploratory [--acknowledge-unverified-inputs] [--dry-run] --out runs/v5

--dry-run builds every design and reports sample sizes per fold WITHOUT fitting or scoring, so
it is safe before the spec is signed off. Historical fitting requires spec status SIGNED_OFF.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.exceptions import ConvergenceWarning

from .crop_weather import crop_features, feature_names, load_crop_spec, load_regions
from .evaluation import calibration_table, probability_metrics
from .features import feature_frame
from .io import Inputs, load_inputs, readiness_blockers, write_json
from .models import TARGET as FIT_TARGET, check_binary, fit_pair
from .parameters import export_model
from .runner import fresh_directory
from .spec import FEATURES, HISTORICAL_STATUS, SYNTHETIC_STATUS, RunConfig, SignalOriginError
from .split import make_split
from .uncertainty import paired_brier_intervals
from .v5_labels import Y, threshold_labels

ROOT = Path(__file__).resolve().parents[1]
SINGLE = ("rain_anom_z", "temp_anom_z")


def load_spec(path) -> dict:
    spec = json.loads(Path(path).read_text())
    need = {"status", "models", "price_history_start", "fold_years", "thresholds_pct",
            "horizons_sessions", "primary_target", "scopes", "uncertainty", "weather_lag_calendar_days"}
    if need - set(spec):
        raise SignalOriginError(f"V5 spec is missing {sorted(need - set(spec))}")
    if not {"B0", "B1"}.issubset(spec["models"]) or set(spec["models"]) - {"B0", "B1", "A1", "A3"}:
        raise SignalOriginError("V5 models must include B0 and B1 and come from B0, B1, A1, A3")
    return spec


def model_features(models, a3_names) -> dict:
    full = {"B0": (), "B1": tuple(FEATURES), "A1": (*FEATURES, *SINGLE), "A3": (*FEATURES, *a3_names)}
    return {m: full[m] for m in models}


def prepare_base(frame, single, crop, lag_days):
    """Price features plus weather joined at exactly t - lag calendar days (V4 used 4)."""
    base = frame[["price_date", "session_index", "close_us_cents_per_lb"]].join(feature_frame(frame))
    base["weather_observation_date"] = base.price_date - pd.Timedelta(days=lag_days)
    w = single[["weather_date_utc", *SINGLE]].copy()
    w["weather_date_utc"] = pd.to_datetime(w.weather_date_utc, errors="raise")
    if crop is not None:
        c = crop.copy()
        c["weather_date_utc"] = pd.to_datetime(c.weather_date_utc, errors="raise")
        w = w.merge(c, on="weather_date_utc", how="outer", validate="one_to_one")
    base = base.merge(w.sort_values("weather_date_utc"), left_on="weather_observation_date",
                      right_on="weather_date_utc", how="left", validate="many_to_one")
    base.index = frame.index
    return base


def build_design(base, frame, h, threshold, feats, mask=None):
    d = base.copy()
    lab = threshold_labels(frame, h, threshold, mask)
    for c in lab:
        d[c] = lab[c]
    cols = sorted({c for fs in feats.values() for c in fs})
    d["features_ready"] = np.isfinite(d[cols].to_numpy(dtype=float)).all(axis=1)
    d["label_ready"] = d[Y].notna()
    d["eligible"] = d.features_ready & d.label_ready  # matched sample: every model, same rows
    return d


def fit_models(train, test, cfg, feats):
    adapter = train.copy(deep=True)
    adapter[FIT_TARGET] = train[Y]
    pair = fit_pair(adapter, cfg)
    pred = pair.predict(test)
    params = {"B0_probability": pair.b0.probability_, "B1": export_model(pair.b1, FEATURES),
              "training_rows": len(train), "training_positives": int(train[Y].sum())}
    y = check_binary(train[Y])
    for name, cols in feats.items():
        if name in ("B0", "B1"):
            continue
        model = clone(pair.b1)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            model.fit(train[list(cols)], y)
        if any(issubclass(c.category, ConvergenceWarning) for c in caught):
            raise SignalOriginError("Convergence failure: " + name)
        idx = int(np.flatnonzero(model.classes_ == 1)[0])
        pred["p_" + name] = model.predict_proba(test[list(cols)])[:, idx]
        params[name] = export_model(model, list(cols))
    return pred[["p_" + m for m in feats]], params


def scored(rows, scope, models):
    recs = [{"scope": scope, "model": m, **probability_metrics(rows[Y], rows["p_" + m])} for m in models]
    t = pd.DataFrame(recs)
    b0 = float(t.loc[t.model.eq("B0"), "brier_score"].iloc[0])
    t["brier_skill_vs_B0"] = 1 - t.brier_score / b0
    t["brier_gain_vs_FLAT50"] = 0.25 - t.brier_score
    return t


def variants(spec, has_mask):
    out = [("grid", t, h) for t in spec["thresholds_pct"] for h in spec["horizons_sessions"]]
    s = spec.get("label_sensitivity")
    if s and has_mask:
        out.append(("liquidity_sensitivity", s["threshold_pct"], s["horizon_sessions"]))
    return out


def analyze(inputs: Inputs, single, region_long, weights, crop_spec, spec, mask=None, *,
            dry_run=False, models=None):
    models = list(models or spec["models"])
    if not set(models) <= set(spec["models"]) or not {"B0", "B1"} <= set(models):
        raise SignalOriginError("--models must be a subset of the spec's models and keep B0 and B1")
    frame = inputs.frame
    start = pd.Timestamp(spec["price_history_start"])
    crop, a3 = None, ()
    if "A3" in models:
        if region_long is None:
            raise SignalOriginError("A3 needs --region-weather (data_tools/pull_power_regions.py output)")
        a3 = feature_names(crop_spec)
        years = range(start.year - 1, int(frame.price_date.dt.year.max()) + 1)
        crop = crop_features(region_long, weights, crop_spec, years_to_build=years)
    feats = model_features(models, a3)
    base = prepare_base(frame, single, crop, spec["weather_lag_calendar_days"])
    out = {k: [] for k in ("predictions", "metrics", "intervals", "annual", "calibration", "counts")}
    params, audits = {}, []
    for variant, thr, h in variants(spec, mask is not None):
        design = build_design(base, frame, h, thr, feats, mask if variant != "grid" else None)
        folds = []
        for year in spec["fold_years"]:
            dates = design.loc[design.price_date.dt.year.eq(year), "price_date"]
            if dates.empty:
                raise SignalOriginError(f"No sessions in fold year {year}")
            cfg = RunConfig(test_start=dates.min().strftime("%Y-%m-%d"), test_end=dates.max().strftime("%Y-%m-%d"),
                            train_start=spec["price_history_start"])
            split = make_split(design, cfg)
            tag = dict(variant=variant, threshold_pct=thr, horizon=h, fold_year=year)
            out["counts"].append({**tag, "train_rows": split.audit["training_rows"], "test_rows": split.audit["test_rows"],
                                  "purged_training_rows": split.audit["purged_training_rows"]})
            audits.append({**tag, **split.audit})
            if dry_run:
                continue
            pred, p = fit_models(split.train, split.test, cfg, feats)
            params[f"{variant}/t{thr}/h{h}/{year}"] = p
            rows = split.test[["price_date", Y, "label_end_date", "first_cross_date"]].join(pred).assign(**tag)
            folds.append(rows)
            out["annual"].append(scored(rows, "annual_fold", models).assign(**tag))
        if dry_run:
            continue
        rows = pd.concat(folds, ignore_index=True).sort_values("price_date")
        out["predictions"].append(rows)
        for scope, (lo, hi) in spec["scopes"].items():
            sub = rows[rows.price_date.dt.year.between(lo, hi)]
            if sub.empty or sub[Y].nunique() < 2:
                continue
            tag = dict(variant=variant, threshold_pct=thr, horizon=h, scope=scope)
            out["metrics"].append(scored(sub, scope, models).assign(**tag))
            u = spec["uncertainty"]
            out["intervals"].append(paired_brier_intervals(sub, models, Y, h, u["n_boot"], u["seed"]).assign(**tag))
            for m in models:
                out["calibration"].append(calibration_table(sub[Y], sub["p_" + m]).assign(model=m, **tag))
    tables = {k: (pd.DataFrame(v) if k == "counts" else pd.concat(v, ignore_index=True))
              for k, v in out.items() if v}
    return tables, params, audits, models


def _git_commit():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              check=True).stdout.strip()
    except Exception:
        return None


def save(tables, params, audits, receipt, out: Path):
    fresh_directory(out)
    write_json(out / "run_receipt.json", {**receipt, "completed": False})
    for name, t in tables.items():
        t.to_csv(out / f"{name}.csv", index=False, float_format="%.10g")
    write_json(out / "fold_audits.json", audits)
    if params:
        write_json(out / "fitted_parameters.json", params)
    write_json(out / "run_receipt.json", {**receipt, "completed": True})


def main(argv=None):
    ap = argparse.ArgumentParser(description="Signal-Origin V5 (offline research; no live forecasting).")
    sub = ap.add_subparsers(dest="command", required=True)
    syn = sub.add_parser("synthetic", help="Run V5 end to end on artificial data only.")
    syn.add_argument("--out", type=Path, required=True)
    syn.add_argument("--spec", type=Path, default=ROOT / "configs" / "v5_spec.json")
    syn.add_argument("--quick", action="store_true", help="three folds, 10%% threshold, 21/63 sessions")
    run = sub.add_parser("run", help="Historical run on independently obtained local inputs.")
    for name in ("spec", "prices", "sessions", "metadata", "weather-features", "out"):
        run.add_argument("--" + name, type=Path, required=True)
    run.add_argument("--region-weather", type=Path)
    run.add_argument("--regions", type=Path, default=ROOT / "configs" / "v5_regions.csv")
    run.add_argument("--crop-windows", type=Path, default=ROOT / "configs" / "v5_crop_windows.json")
    run.add_argument("--liquidity", type=Path, help="price_date, crossing_eligible (data_tools/make_liquidity_mask.py)")
    run.add_argument("--models", nargs="+", help="subset of spec models, e.g. B0 B1 A1 before the region pull")
    run.add_argument("--dry-run", action="store_true", help="sample sizes only; no fitting or scoring")
    run.add_argument("--acknowledge-exploratory", action="store_true")
    run.add_argument("--acknowledge-unverified-inputs", action="store_true",
                     help="proceed when the input gate lists blockers (e.g. unverified calendar); blockers are recorded")
    a = ap.parse_args(argv)
    try:
        if a.out.exists() and any(a.out.iterdir()):
            raise SignalOriginError("Use a new or empty output directory.")
        spec = load_spec(a.spec)
        spec_sha = hashlib.sha256(Path(a.spec).read_bytes()).hexdigest()
        if a.command == "synthetic":
            from .synthetic_v5 import make_inputs
            inputs, single, long, weights, liquidity = make_inputs()
            crop_spec = load_crop_spec(ROOT / "configs" / "v5_crop_windows.json")
            if a.quick:
                spec = {**spec, "fold_years": [2024, 2025, 2026], "thresholds_pct": [10],
                        "horizons_sessions": [21, 63], "price_history_start": "2019-01-02"}
            tables, params, audits, models = analyze(inputs, single, long, weights, crop_spec, spec, liquidity)
            status, blockers, dry = SYNTHETIC_STATUS, [], False
        else:
            if not a.acknowledge_exploratory:
                raise SignalOriginError("Explicit --acknowledge-exploratory is required.")
            inputs = load_inputs(a.prices, a.sessions, a.metadata)
            if inputs.metadata["data_kind"] != "historical":
                raise SignalOriginError("Use the synthetic command for synthetic inputs.")
            blockers = readiness_blockers(inputs.metadata)
            if blockers and not a.acknowledge_unverified_inputs:
                raise SignalOriginError("Input gate: " + " ".join(blockers) +
                                        " Re-run with --acknowledge-unverified-inputs to proceed exploratorily; blockers are recorded.")
            if not a.dry_run and (spec["status"] != "SIGNED_OFF" or len(spec.get("signed_off_by", [])) < 2):
                raise SignalOriginError("Spec is not SIGNED_OFF by both teammates. Only --dry-run is allowed.")
            single = pd.read_csv(a.weather_features)
            long = pd.read_csv(a.region_weather) if a.region_weather else None
            mask = None
            if a.liquidity:
                m = pd.read_csv(a.liquidity, parse_dates=["price_date"]).set_index("price_date").crossing_eligible
                mask = m.reindex(inputs.frame.price_date).fillna(False).astype(bool).set_axis(inputs.frame.index)
            tables, params, audits, models = analyze(
                inputs, single, long, load_regions(a.regions), load_crop_spec(a.crop_windows), spec, mask,
                dry_run=a.dry_run, models=a.models)
            status, dry = HISTORICAL_STATUS, a.dry_run
        receipt = {"version": "V5", "evidence_status": status, "dry_run": dry, "models_run": models,
                   "spec_status": spec["status"], "spec_sha256": spec_sha, "git_commit": _git_commit(),
                   "input_gate_blockers_acknowledged": blockers,
                   "input_sha256": inputs.audit.get("input_sha256", {}),
                   "forecasting_skill_established": False,
                   "dependencies": {n: importlib.metadata.version(n) for n in ("numpy", "pandas", "scikit-learn")}}
        save(tables, params, audits, receipt, a.out)
        print(f"Completed V5 {'dry run' if dry else status}: {a.out}")
        return 0
    except (SignalOriginError, ValueError, OSError, KeyError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
