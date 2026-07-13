"""Aggregate-only data-quality summaries."""

import pandas as pd


def summarize(frame: pd.DataFrame) -> dict[str, object]:
    return {
        "row_count": len(frame),
        "column_count": len(frame.columns),
        "missing_rates": {name: round(float(value), 6) for name, value in frame.isna().mean().items()},
    }
