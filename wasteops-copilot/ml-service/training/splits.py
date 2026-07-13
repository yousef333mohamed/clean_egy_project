"""Chronological train/validation/test splits for temporal data."""

from dataclasses import dataclass
import pandas as pd


@dataclass(frozen=True)
class TemporalSplit:
    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame


def chronological_split(frame: pd.DataFrame, timestamp_column: str, train_fraction: float = 0.6, validation_fraction: float = 0.2) -> TemporalSplit:
    if not 0 < train_fraction < 1 or not 0 < validation_fraction < 1 or train_fraction + validation_fraction >= 1:
        raise ValueError("Invalid split fractions")
    ordered = (
        frame.assign(_split_timestamp=pd.to_datetime(frame[timestamp_column], utc=True, errors="raise"))
        .sort_values("_split_timestamp")
        .drop(columns="_split_timestamp")
    )
    first = max(1, int(len(ordered) * train_fraction))
    second = max(first + 1, int(len(ordered) * (train_fraction + validation_fraction)))
    if second >= len(ordered):
        raise ValueError("Not enough rows for chronological train/validation/test splits")
    return TemporalSplit(ordered.iloc[:first].copy(), ordered.iloc[first:second].copy(), ordered.iloc[second:].copy())


def assert_no_temporal_overlap(split: TemporalSplit, timestamp_column: str) -> None:
    train = pd.to_datetime(split.train[timestamp_column], utc=True)
    validation = pd.to_datetime(split.validation[timestamp_column], utc=True)
    test = pd.to_datetime(split.test[timestamp_column], utc=True)
    if train.max() >= validation.min() or validation.max() >= test.min():
        raise ValueError("Temporal leakage: split periods overlap")
