"""Strategy logic for CSI500 momentum with HS300 trend filter."""

import pandas as pd

from src.research.universe import filter_universe
from src.research.factors import momentum_120


def hs300_trend_filter(index_df: pd.DataFrame, date: pd.Timestamp) -> bool:
    """Allow holding only when HS300 close > 120-day MA."""
    df = index_df[index_df["date"] <= date].copy()
    if len(df) < 120:
        return False
    df["ma120"] = df["close"].rolling(120).mean()
    last = df.iloc[-1]
    return float(last["close"]) > float(last["ma120"])


def rank_momentum(
    date: pd.Timestamp,
    components: pd.DataFrame,
    daily_map: dict[str, pd.DataFrame],
) -> list[tuple[str, float]]:
    """Rank universe by 120-day momentum."""
    universe = filter_universe(date, components, daily_map)
    scores = []
    for sym in universe:
        df = daily_map.get(sym)
        df = df[df["date"] <= date]
        score = momentum_120(df)
        if score is None:
            continue
        scores.append((sym, score))

    scores.sort(key=lambda x: x[1], reverse=True)
    return scores


def pick_topn(
    date: pd.Timestamp,
    components: pd.DataFrame,
    daily_map: dict[str, pd.DataFrame],
    topn: int,
) -> list[str]:
    """Pick top N stocks by 120-day momentum."""
    scores = rank_momentum(date, components, daily_map)
    return [s for s, _ in scores[:topn]]
