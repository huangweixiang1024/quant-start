"""Factor calculations."""

import pandas as pd


def momentum_120(df: pd.DataFrame) -> float | None:
    """120-day momentum based on close prices.

    TODO: use forward-adjusted close if available.
    """
    if df is None or len(df) < 120:
        return None
    df = df.sort_values("date")
    start = df.iloc[-120]["close"]
    end = df.iloc[-1]["close"]
    if start == 0:
        return None
    return float(end / start - 1.0)
