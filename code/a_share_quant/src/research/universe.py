"""Universe selection and filters."""

import pandas as pd


def is_st(name: str | None) -> bool:
    """Check if a stock is ST or *ST by name."""
    if not name:
        return False
    return "ST" in name.upper()


def filter_universe(
    date: pd.Timestamp,
    components: pd.DataFrame,
    daily_map: dict[str, pd.DataFrame],
    min_avg_amount: float = 1e8,
) -> list[str]:
    """Filter universe by ST, suspension, and liquidity.

    Suspension filter is approximated by volume == 0 (TODO: use official field if available).
    Amount is approximated by close * volume (unit differences may exist).
    """
    date = pd.Timestamp(date)
    symbols = []
    for _, row in components.iterrows():
        sym = row.get("symbol")
        name = row.get("name")
        if not sym or is_st(name):
            continue

        df = daily_map.get(sym)
        if df is None or df.empty:
            continue

        df = df[df["date"] <= date]
        if len(df) < 20:
            continue

        last = df.iloc[-1]
        if "volume" in df.columns and float(last["volume"]) == 0:
            continue

        df_tail = df.tail(20)
        amount = df_tail["close"] * df_tail["volume"]
        if amount.mean() < min_avg_amount:
            continue

        symbols.append(sym)

    return symbols
