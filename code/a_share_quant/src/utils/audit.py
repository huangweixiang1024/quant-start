"""Audit helpers for backtest outputs."""

import argparse
import pandas as pd

from src.data.store import index_path, nav_path, positions_path, trades_path, read_parquet
from src.data.calendar import TradingCalendar


def check_continuous_dates(nav_df: pd.DataFrame, calendar: TradingCalendar) -> tuple[bool, int]:
    """Check NAV dates are continuous based on trading calendar."""
    if nav_df.empty:
        return False, 0
    dates = pd.to_datetime(nav_df["date"]).sort_values().unique()
    expected = calendar.between(dates[0], dates[-1])
    missing = set(expected) - set(dates)
    return len(missing) == 0, len(missing)


def check_positions_unique(positions_df: pd.DataFrame) -> tuple[bool, int]:
    """Check (date, symbol) uniqueness for positions."""
    if positions_df.empty:
        return True, 0
    dup = positions_df.duplicated(subset=["date", "symbol"]).sum()
    return dup == 0, int(dup)


def check_trades_unique(trades_df: pd.DataFrame) -> tuple[bool, int]:
    """Check (date, symbol, side) uniqueness for trades."""
    if trades_df.empty:
        return True, 0
    dup = trades_df.duplicated(subset=["date", "symbol", "side"]).sum()
    return dup == 0, int(dup)


def check_weights(positions_df: pd.DataFrame, tol: float = 0.05) -> tuple[bool, int]:
    """Check sum of weights per date is close to 1 within tolerance."""
    if positions_df.empty:
        return True, 0
    sums = positions_df.groupby("date")["weight"].sum()
    bad = sums[(sums < 1 - tol) | (sums > 1 + tol)]
    return len(bad) == 0, int(len(bad))


def run_audit(tol: float = 0.05) -> None:
    """Run audit checks against cached data."""
    idx_df = read_parquet(index_path())
    calendar = TradingCalendar(idx_df)

    nav_df = read_parquet(nav_path()) if nav_path().exists() else pd.DataFrame()
    pos_df = read_parquet(positions_path()) if positions_path().exists() else pd.DataFrame()
    trd_df = read_parquet(trades_path()) if trades_path().exists() else pd.DataFrame()

    ok_nav, missing = check_continuous_dates(nav_df, calendar)
    ok_pos, dup_pos = check_positions_unique(pos_df)
    ok_trd, dup_trd = check_trades_unique(trd_df)
    ok_wgt, bad_wgt = check_weights(pos_df, tol=tol)

    print(f"NAV 连续性 / nav continuous: {ok_nav}; missing: {missing}")
    print(f"positions 唯一性 / positions unique: {ok_pos}; duplicates: {dup_pos}")
    print(f"trades 唯一性 / trades unique: {ok_trd}; duplicates: {dup_trd}")
    print(f"权重校验 / weight check: {ok_wgt}; bad dates: {bad_wgt}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit backtest outputs")
    parser.add_argument("--tol", type=float, default=0.05, help="weight sum tolerance")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_audit(tol=args.tol)
