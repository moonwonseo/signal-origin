"""Frozen midterm specification; these are project choices, not fitted parameters."""
from dataclasses import asdict, dataclass, fields
from datetime import date
import math
from typing import Any

HORIZON = 63
THRESHOLD = "1.10"
FEATURES = ("ret21", "ret63", "vol63", "sin_doy", "cos_doy")
SYNTHETIC_STATUS = "SYNTHETIC_SOFTWARE_TEST_ONLY"
HISTORICAL_STATUS = "RETROSPECTIVE_RESEARCH_NOT_LIVE_VALIDATION"

class SignalOriginError(ValueError):
    """An actionable input, configuration, or research-readiness error."""


def iso_date(value: str, name: str) -> str:
    if not isinstance(value, str):
        raise SignalOriginError(f"{name} must be an ISO date YYYY-MM-DD.")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise SignalOriginError(f"{name} must be an ISO date YYYY-MM-DD: {value!r}") from exc
    if parsed.isoformat() != value:
        raise SignalOriginError(f"{name} must use YYYY-MM-DD, not {value!r}.")
    return value


@dataclass(frozen=True)
class RunConfig:
    """A single frozen chronological holdout, with no tuning on its scores."""
    test_start: str
    test_end: str | None = None
    train_start: str | None = None
    C: float = 1.0
    max_iter: int = 2000
    tolerance: float = 1e-8
    min_train_rows: int = 252
    min_test_rows: int = 30
    min_train_per_class: int = 10
    calibration_bins: int = 5
    seed: int = 42

    def __post_init__(self) -> None:
        iso_date(self.test_start, "test_start")
        for name in ("test_end", "train_start"):
            value = getattr(self, name)
            if value is not None:
                iso_date(value, name)
        if self.test_end is not None and self.test_end < self.test_start:
            raise SignalOriginError("test_end precedes test_start.")
        if self.train_start is not None and self.train_start >= self.test_start:
            raise SignalOriginError("train_start must precede test_start.")
        for name in ("C", "tolerance"):
            x = getattr(self, name)
            if isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) or x <= 0:
                raise SignalOriginError(f"{name} must be finite and positive.")
        for name in ("max_iter", "min_train_rows", "min_test_rows", "min_train_per_class", "calibration_bins"):
            x = getattr(self, name)
            if type(x) is not int or x < 1:
                raise SignalOriginError(f"{name} must be a positive integer.")
        if not 2 <= self.calibration_bins <= 20:
            raise SignalOriginError("calibration_bins must be between 2 and 20.")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise SignalOriginError("seed must be an integer between 0 and 2**32-1.")

    @classmethod
    def from_dict(cls, values: dict[str, Any]) -> "RunConfig":
        if not isinstance(values, dict):
            raise SignalOriginError("Configuration must be a JSON object.")
        extra = set(values) - {f.name for f in fields(cls)}
        if extra:
            raise SignalOriginError(f"Unknown configuration fields: {sorted(extra)}. The target is fixed at +10%, 63 sessions.")
        if not values.get("test_start"):
            raise SignalOriginError("Set test_start BEFORE evaluating historical results; the template intentionally leaves it null.")
        return cls(**values)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
