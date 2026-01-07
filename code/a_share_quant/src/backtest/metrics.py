"""Performance metrics."""

import pandas as pd
import numpy as np


def summarize_metrics(nav: pd.DataFrame) -> dict:
    """Calculate basic performance metrics."""
    df = nav.copy()
    df = df.sort_values("date")
    df["ret"] = df["nav"].pct_change().fillna(0.0)

    ann = (1 + df["ret"]).prod() ** (252 / max(1, len(df))) - 1
    vol = df["ret"].std() * np.sqrt(252)
    sharpe = 0.0 if df["ret"].std() == 0 else (df["ret"].mean() / df["ret"].std()) * np.sqrt(252)

    roll_max = df["nav"].cummax()
    dd = df["nav"] / roll_max - 1
    mdd = dd.min()

    monthly = df.set_index("date")["ret"].resample("ME").apply(lambda x: (1 + x).prod() - 1)
    win_rate = float((monthly > 0).mean()) if len(monthly) > 0 else 0.0

    return {
        "ann_return": float(ann),
        "volatility": float(vol),
        "sharpe": float(sharpe),
        "max_drawdown": float(mdd),
        "monthly_win_rate": float(win_rate),
    }
