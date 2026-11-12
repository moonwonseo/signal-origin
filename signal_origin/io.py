"""Strict local-file input, provenance gates, and calendar-preserving alignment.

No downloads, unit conversions, forward fills, inferred exchange holidays, or
contract-roll adjustments occur in this module.
"""
import csv
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from jsonschema import Draft202012Validator

from .spec import HISTORICAL_STATUS, SYNTHETIC_STATUS, SignalOriginError, iso_date

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def load_json(path: str | Path) -> dict[str, Any]:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise SignalOriginError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    def invalid_constant(value):
        raise SignalOriginError(f"Non-standard JSON value: {value}")
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"),
                           object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (OSError, json.JSONDecodeError) as exc:
        raise SignalOriginError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SignalOriginError(f"JSON {path} must contain an object.")
    return value


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def read_csv_text(path: str | Path, required: set[str]) -> pd.DataFrame:
    path = Path(path)
    try:
        with path.open(encoding="utf-8-sig", newline="") as handle:
            header = next(csv.reader(handle), [])
        if len(header) != len(set(header)):
            raise SignalOriginError(f"Duplicate column names in {path.name}.")
        if not required.issubset(header):
            raise SignalOriginError(f"{path.name} needs columns {sorted(required)}; got {header}.")
        df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as exc:
        raise SignalOriginError(f"Cannot read CSV {path}: {exc}") from exc
    if df.empty:
        raise SignalOriginError(f"{path.name} contains no rows; a header-only template is not data.")
    return df


def parse_dates(series: pd.Series, name: str) -> pd.Series:
    for value in series:
        iso_date(value, name)
    try:
        dates = pd.to_datetime(series, format="%Y-%m-%d", errors="raise")
    except (ValueError, OverflowError) as exc:
        raise SignalOriginError(f"Invalid date in {name}: {exc}") from exc
    if dates.duplicated().any():
        raise SignalOriginError(f"Duplicate dates in {name}: {list(series[dates.duplicated()].head(5))}")
    return dates


@dataclass
class Inputs:
    frame: pd.DataFrame
    metadata: dict[str, Any]
    audit: dict[str, Any]
    paths: dict[str, Path]

    @property
    def evidence_status(self) -> str:
        return SYNTHETIC_STATUS if self.metadata["data_kind"] == "synthetic" else HISTORICAL_STATUS


def check_metadata(meta: dict[str, Any]) -> None:
    schema = load_json(Path(__file__).with_name("schema") / "metadata.schema.json")
    errors = sorted(Draft202012Validator(schema).iter_errors(meta), key=lambda e: str(e.path))
    if errors:
        details = "; ".join(f"{'.'.join(str(x) for x in e.path) or 'metadata'}: {e.message}" for e in errors[:5])
        raise SignalOriginError(f"Metadata does not match schema: {details}")
    try:
        stamp = datetime.fromisoformat(meta["retrieved_at_utc"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise SignalOriginError("retrieved_at_utc must be a timezone-aware ISO timestamp.") from exc
    if stamp.utcoffset() != timezone.utc.utcoffset(stamp):
        raise SignalOriginError("retrieved_at_utc must explicitly use UTC (Z or +00:00).")
    if meta["data_kind"] == "historical" and meta["instrument"] != "ICE_COFFEE_C":
        raise SignalOriginError("Historical inputs must be ICE_COFFEE_C. FRED/ICO are not silently substituted.")
    if meta["data_kind"] == "synthetic" and meta["instrument"] != "SYNTHETIC_TEST_SERIES":
        raise SignalOriginError("Synthetic inputs must identify SYNTHETIC_TEST_SERIES.")


def readiness_blockers(meta: dict[str, Any]) -> list[str]:
    blockers = []
    if not meta["calendar_verified"]:
        blockers.append("Expected session calendar is not marked verified; row counts cannot certify 63 exchange sessions.")
    if meta["roll_adjustment_status"] != "documented_return_compatible":
        blockers.append("Continuous-series/roll construction is unverified; document return compatibility before modeling.")
    return blockers


def load_inputs(prices: str | Path, sessions: str | Path, metadata: str | Path) -> Inputs:
    paths = {"prices": Path(prices), "sessions": Path(sessions), "metadata": Path(metadata)}
    meta = load_json(paths["metadata"])
    check_metadata(meta)
    raw = read_csv_text(paths["prices"], {"price_date", "close_us_cents_per_lb"})
    calendar = read_csv_text(paths["sessions"], {"session_date"})
    raw["price_date"] = parse_dates(raw["price_date"], "price_date")
    calendar["session_date"] = parse_dates(calendar["session_date"], "session_date")
    sorted_input = bool(raw["price_date"].is_monotonic_increasing)
    calendar = calendar.sort_values("session_date").reset_index(drop=True)
    raw = raw.sort_values("price_date").reset_index(drop=True)
    gaps = calendar["session_date"].diff().dt.days.dropna()
    if len(gaps) >= 3 and gaps.median() > 7:
        raise SignalOriginError("Session list is too sparse for daily exchange data; do not supply monthly or weekly samples.")
    outside = raw.loc[~raw["price_date"].isin(calendar["session_date"]), "price_date"]
    if len(outside):
        raise SignalOriginError(f"Price dates outside supplied session calendar: {list(outside.dt.strftime('%Y-%m-%d').head(5))}")
    if raw["price_date"].min() != calendar["session_date"].min() or raw["price_date"].max() != calendar["session_date"].max():
        raise SignalOriginError("Price CSV and session CSV must have the same first and last dates. Use blank prices for missing edge sessions; do not extend a calendar into the future.")
    status_supplied = "quality_status" in raw.columns
    if not status_supplied:
        raw["quality_status"] = np.where(raw["close_us_cents_per_lb"].str.strip().eq(""), "missing", "ok")
    raw["quality_status"] = raw["quality_status"].str.strip().str.lower()
    allowed = {"ok", "missing", "review", "excluded"}
    unknown = set(raw["quality_status"]) - allowed
    if unknown:
        raise SignalOriginError(f"Unknown quality_status {sorted(unknown)}; use ok, missing, review, or excluded.")
    numeric = []
    decimal_text = []
    for date_value, text in zip(raw["price_date"], raw["close_us_cents_per_lb"]):
        text = text.strip()
        if text == "":
            numeric.append(np.nan)
            decimal_text.append("")
            continue
        try:
            value = Decimal(text)
            fvalue = float(value)
        except (InvalidOperation, ValueError, OverflowError) as exc:
            raise SignalOriginError(f"Non-numeric price on {date_value.date()}: {text!r}. Blank unresolved values instead.") from exc
        if not value.is_finite() or not np.isfinite(fvalue) or fvalue <= 0:
            raise SignalOriginError(f"Price must be finite and positive on {date_value.date()}: {text!r}.")
        numeric.append(fvalue)
        decimal_text.append(str(value))
    raw["raw_price_text"] = decimal_text
    raw["close_us_cents_per_lb"] = numeric
    # Preserve the calendar even when a row has been omitted by the provider.
    frame = calendar.rename(columns={"session_date": "price_date"}).merge(raw, how="left", on="price_date", validate="one_to_one")
    frame["quality_status"] = frame["quality_status"].fillna("missing")
    frame["raw_price_text"] = frame["raw_price_text"].fillna("")
    frame["price_usable"] = frame["quality_status"].eq("ok") & frame["close_us_cents_per_lb"].notna()
    frame["model_price"] = frame["close_us_cents_per_lb"].where(frame["price_usable"])
    frame["session_index"] = np.arange(len(frame), dtype=int)
    warnings = [
        "Source, calendar, and roll verification are supplied declarations, not independent publisher certification.",
        "Research forecast origin is after the selected closing/settlement value is available; no execution at that price is assumed.",
        "One historical price snapshot does not by itself establish point-in-time revision safety.",
    ]
    if not status_supplied:
        warnings.append("No row quality_status supplied: numeric observations treated as structurally usable, not substantively certified.")
    if len(gaps) and gaps.max() > 7:
        warnings.append("Session-calendar gap longer than 7 calendar days: verify closures/completeness against the source.")
    if not sorted_input:
        warnings.append("Price rows were sorted chronologically; raw input hash retained.")
    audit = {
        "data_kind": meta["data_kind"],
        "evidence_status": SYNTHETIC_STATUS if meta["data_kind"] == "synthetic" else HISTORICAL_STATUS,
        "source_rows": len(raw), "expected_sessions": len(frame),
        "inserted_missing_session_rows": len(frame) - len(raw),
        "usable_prices": int(frame["price_usable"].sum()),
        "unusable_prices": int((~frame["price_usable"]).sum()),
        "start_date": frame["price_date"].min().strftime("%Y-%m-%d"),
        "end_date": frame["price_date"].max().strftime("%Y-%m-%d"),
        "quality_status_counts": {str(k): int(v) for k, v in frame["quality_status"].value_counts().items()},
        "extra_price_columns_ignored_by_model": sorted(set(raw.columns) - {"price_date", "close_us_cents_per_lb", "quality_status", "raw_price_text"}),
        "model_readiness_blockers": readiness_blockers(meta), "warnings": warnings,
        "input_sha256": {k: sha256_file(v) for k, v in paths.items()},
    }
    return Inputs(frame, meta, audit, paths)


def require_model_ready(inputs: Inputs, allow_synthetic: bool = False) -> None:
    if inputs.metadata["data_kind"] == "synthetic" and not allow_synthetic:
        raise SignalOriginError("Synthetic files require --allow-synthetic. They cannot be presented as real-data results.")
    blockers = readiness_blockers(inputs.metadata)
    if blockers:
        raise SignalOriginError("Input gate blocked modeling: " + " ".join(blockers))
