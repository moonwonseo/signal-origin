"""B0 empirical training frequency and B1 train-only-scaled logistic regression."""
from dataclasses import dataclass
import warnings

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .spec import FEATURES, RunConfig, SignalOriginError

TARGET = "target_up_10pct_63_sessions"


def check_binary(y) -> np.ndarray:
    arr = np.asarray(y, dtype=float)
    if arr.ndim != 1 or not arr.size or not np.isfinite(arr).all() or not np.isin(arr, [0, 1]).all():
        raise SignalOriginError("Targets must be a nonempty, finite, one-dimensional array of 0 or 1.")
    return arr.astype(int)


class HistoricalFrequency:
    """One constant probability, estimated ONLY from the given training labels."""
    def fit(self, y) -> "HistoricalFrequency":
        labels = check_binary(y)
        self.probability_ = float(labels.mean())
        self.n_train_ = len(labels)
        return self

    def predict_proba(self, n: int) -> np.ndarray:
        if not hasattr(self, "probability_"):
            raise SignalOriginError("Fit B0 before predicting.")
        if type(n) is not int or n < 0:
            raise SignalOriginError("n must be a nonnegative integer.")
        return np.full(n, self.probability_, dtype=float)


@dataclass
class ModelPair:
    b0: HistoricalFrequency
    b1: Pipeline
    train_class_counts: dict[str, int]
    optimizer_iterations: int

    def predict(self, frame: pd.DataFrame) -> pd.DataFrame:
        X = frame.loc[:, list(FEATURES)]
        if not np.isfinite(X.to_numpy(dtype=float)).all():
            raise SignalOriginError("B1 prediction features must be finite. No inference-time imputation is performed.")
        positive_index = int(np.flatnonzero(self.b1.classes_ == 1)[0])
        result = pd.DataFrame(index=frame.index)
        result["p_B0"] = self.b0.predict_proba(len(frame))
        result["p_B1"] = self.b1.predict_proba(X)[:, positive_index]
        return result

    def export(self) -> dict:
        scaler = self.b1.named_steps["scale"]
        model = self.b1.named_steps["logit"]
        return {
            "feature_order": list(FEATURES), "positive_class": 1,
            "B0_probability": self.b0.probability_,
            "B0_training_rows": self.b0.n_train_,
            "scaler_mean": scaler.mean_.tolist(), "scaler_scale": scaler.scale_.tolist(),
            "B1_coefficients_standardized": model.coef_[0].tolist(),
            "B1_intercept": float(model.intercept_[0]),
            "training_class_counts": self.train_class_counts,
            "optimizer_iterations": self.optimizer_iterations,
            "interpretation": "Coefficients act on standardized features and describe association, not causation. Export is JSON, not an executable pickle.",
        }


def fit_pair(train: pd.DataFrame, config: RunConfig) -> ModelPair:
    X = train.loc[:, list(FEATURES)]
    y = check_binary(train[TARGET])
    if not np.isfinite(X.to_numpy(dtype=float)).all():
        raise SignalOriginError("Training features are incomplete or non-finite.")
    counts = {str(label): int((y == label).sum()) for label in (0, 1)}
    if min(counts.values()) < config.min_train_per_class:
        raise SignalOriginError(f"B1 needs at least {config.min_train_per_class} matured training examples of each class; got {counts}. Do not fabricate a class or silently replace logistic regression.")
    b0 = HistoricalFrequency().fit(y)
    model = Pipeline([
        ("scale", StandardScaler()),
        ("logit", LogisticRegression(C=config.C, solver="lbfgs", l1_ratio=0.0,
                                     class_weight=None, fit_intercept=True,
                                     max_iter=config.max_iter, tol=config.tolerance,
                                     random_state=config.seed)),
    ])
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always", ConvergenceWarning)
        model.fit(X, y)
    if any(issubclass(w.category, ConvergenceWarning) for w in captured):
        raise SignalOriginError("Logistic regression did not converge. No performance report was exported. Inspect scaling/inputs or increase max_iter without tuning on holdout scores.")
    return ModelPair(b0, model, counts, int(model.named_steps["logit"].n_iter_[0]))


def predict_from_export(frame: pd.DataFrame, export: dict) -> np.ndarray:
    """Reproduce B1 probabilities from the safe JSON parameter export."""
    if export.get("feature_order") != list(FEATURES):
        raise SignalOriginError("Export has the wrong feature order.")
    X = frame.loc[:, list(FEATURES)].to_numpy(dtype=float)
    means = np.asarray(export["scaler_mean"], dtype=float)
    scales = np.asarray(export["scaler_scale"], dtype=float)
    coefs = np.asarray(export["B1_coefficients_standardized"], dtype=float)
    if any(a.shape != (len(FEATURES),) for a in (means, scales, coefs)):
        raise SignalOriginError("Export parameter lengths do not match the feature schema.")
    intercept = float(export["B1_intercept"])
    if not all(np.isfinite(a).all() for a in (X, means, scales, coefs)) or not np.isfinite(intercept) or (scales <= 0).any():
        raise SignalOriginError("Non-finite/invalid exported parameters or prediction features.")
    return expit(((X - means) / scales) @ coefs + intercept)
