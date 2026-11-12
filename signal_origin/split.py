"""Explicit, date-based chronological holdout with matured-label purging."""
from dataclasses import dataclass
import pandas as pd
from .spec import HORIZON, RunConfig, SignalOriginError


@dataclass
class ChronologicalSplit:
    train: pd.DataFrame
    test: pd.DataFrame
    membership: pd.DataFrame
    audit: dict


def make_split(design: pd.DataFrame, config: RunConfig) -> ChronologicalSplit:
    start = pd.Timestamp(config.test_start)
    dates = design["price_date"]
    if start not in set(dates):
        raise SignalOriginError("test_start must be a session in the supplied calendar, not a guessed business day.")
    end = pd.Timestamp(config.test_end) if config.test_end else dates.max()
    eligible = design["eligible"]
    train_window = dates < start
    if config.train_start:
        train_window &= dates >= pd.Timestamp(config.train_start)
    test_window = (dates >= start) & (dates <= end)
    matured = design["label_end_date"] < start
    train_mask = train_window & eligible & matured
    purge_mask = train_window & eligible & ~matured
    test_mask = test_window & eligible
    train = design.loc[train_mask].copy()
    test = design.loc[test_mask].copy()
    if len(train) < config.min_train_rows:
        raise SignalOriginError(f"Only {len(train)} eligible training rows AFTER purging; need at least {config.min_train_rows}. Acquire more history; do not remove the 63-session safeguard.")
    if len(test) < config.min_test_rows:
        raise SignalOriginError(f"Only {len(test)} eligible test rows; need at least {config.min_test_rows}. Check lookback, missing prices, and incomplete future endpoints.")
    if not (train["label_end_date"] < start).all():
        raise SignalOriginError("Internal error: unmatured training outcome crossed the test boundary.")
    membership = design[["price_date", "label_end_date", "features_ready", "label_ready", "eligible"]].copy()
    membership["partition"] = "unused"
    membership.loc[train_window, "partition"] = "pretest_not_eligible"
    membership.loc[test_window, "partition"] = "test_not_eligible"
    membership.loc[purge_mask, "partition"] = "purged_training_outcome_at_or_after_test_start"
    membership.loc[train_mask, "partition"] = "train"
    membership.loc[test_mask, "partition"] = "test"
    if config.train_start:
        membership.loc[dates < pd.Timestamp(config.train_start), "partition"] = "before_train_start"
    membership.loc[dates > end, "partition"] = "after_test_end"
    audit = {
        "split_kind": "single_fixed_chronological_holdout_no_tuning",
        "test_start_requested": config.test_start, "test_end_requested": config.test_end,
        "train_start_requested": config.train_start,
        "train_origin_start": train["price_date"].min().strftime("%Y-%m-%d"),
        "train_origin_end": train["price_date"].max().strftime("%Y-%m-%d"),
        "latest_training_outcome_date": train["label_end_date"].max().strftime("%Y-%m-%d"),
        "test_origin_start": test["price_date"].min().strftime("%Y-%m-%d"),
        "test_origin_end": test["price_date"].max().strftime("%Y-%m-%d"),
        "latest_test_outcome_date": test["label_end_date"].max().strftime("%Y-%m-%d"),
        "training_rows": len(train), "test_rows": len(test), "purged_training_rows": int(purge_mask.sum()),
        "test_window_calendar_sessions": int(test_window.sum()),
        "test_rows_excluded_incomplete_features": int((test_window & ~design["features_ready"]).sum()),
        "test_rows_excluded_missing_endpoint": int((test_window & ~design["label_ready"]).sum()),
        "all_training_outcomes_strictly_before_test_start": True,
        "horizon_exchange_sessions": HORIZON,
        "refitting_in_test": False,
        "warning": "Overlapping 63-session targets are dependent. Counts are forecast origins, not independent market events. No IID confidence intervals or significance claim are produced.",
    }
    return ChronologicalSplit(train, test, membership, audit)


def nonoverlapping_origins(test: pd.DataFrame) -> pd.Index:
    """Greedy chronological, strictly disjoint CLOSED [t,t+63] target windows.

    This is a diagnostic, NOT proof of statistical independence. No score is
    consulted when choosing these dates.
    """
    chosen = []
    previous_end = pd.Timestamp.min
    for index, row in test.sort_values("price_date").iterrows():
        if row["price_date"] > previous_end:
            chosen.append(index)
            previous_end = row["label_end_date"]
    return pd.Index(chosen)
