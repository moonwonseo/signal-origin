"""Probability metrics and descriptive calibration, not trading performance."""
import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from .models import check_binary
from .spec import SignalOriginError


def checked_probabilities(p, n: int) -> np.ndarray:
    arr = np.asarray(p, dtype=float)
    if arr.shape != (n,) or not np.isfinite(arr).all() or ((arr < 0) | (arr > 1)).any():
        raise SignalOriginError("Probabilities must be finite, between 0 and 1, and aligned one-to-one with targets.")
    return arr


def probability_metrics(y, p) -> dict:
    y = check_binary(y)
    p = checked_probabilities(p, len(y))
    return {
        "n_forecasts": len(y), "positive_outcomes": int(y.sum()),
        "observed_event_frequency": float(y.mean()), "mean_predicted_probability": float(p.mean()),
        # Explicit binary [0,1] scale; no dependency on a changing API default.
        "brier_score": float(brier_score_loss(y, p, pos_label=1, scale_by_half=True)),
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None,
        "roc_auc_status": "computed" if len(np.unique(y)) == 2 else "undefined_single_class",
    }


def metrics_table(y, predictions: pd.DataFrame, sample: str) -> pd.DataFrame:
    records = []
    for name in ("B0", "B1"):
        records.append({"model": name, "sample": sample, **probability_metrics(y, predictions[f"p_{name}"])})
    table = pd.DataFrame(records)
    b0_score = float(table.loc[table["model"].eq("B0"), "brier_score"].iloc[0])
    table["brier_improvement_vs_B0"] = b0_score - table["brier_score"]
    return table


def calibration_table(y, p, bins: int = 5) -> pd.DataFrame:
    y = check_binary(y)
    p = checked_probabilities(p, len(y))
    if type(bins) is not int or not 2 <= bins <= 20:
        raise SignalOriginError("Use between 2 and 20 fixed calibration bins.")
    edges = np.linspace(0.0, 1.0, bins + 1)
    ids = np.minimum(np.searchsorted(edges, p, side="right") - 1, bins - 1)
    records = []
    for k in range(bins):
        mask = ids == k
        records.append({
            "bin": k, "lower_bound_inclusive": float(edges[k]),
            "upper_bound": float(edges[k + 1]), "upper_bound_inclusive": k == bins - 1,
            "n_forecasts": int(mask.sum()),
            "mean_predicted_probability": float(p[mask].mean()) if mask.any() else None,
            "observed_event_frequency": float(y[mask].mean()) if mask.any() else None,
        })
    return pd.DataFrame(records)
