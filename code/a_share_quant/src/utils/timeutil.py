"""Time utilities for trading calendar alignment."""

import pandas as pd


def to_ts(val) -> pd.Timestamp:
    """Convert input to pandas.Timestamp."""
    return pd.Timestamp(val)


def normalize_dates(df: pd.DataFrame, col: str = "date") -> pd.DataFrame:
    """Ensure a date column is pandas.Timestamp and sorted."""
    out = df.copy()
    out[col] = pd.to_datetime(out[col])
    out = out.sort_values(col).reset_index(drop=True)
    return out
