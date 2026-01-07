"""Backtest engine."""

import pandas as pd

from src.data.store import daily_path, read_parquet
from src.backtest.strategy_csi500_mom import hs300_trend_filter, pick_topn, rank_momentum


def _load_daily(symbols: list[str]) -> dict[str, pd.DataFrame]:
    daily_map = {}
    for sym in symbols:
        path = daily_path(sym)
        if path.exists():
            df = read_parquet(path)
            df["date"] = pd.to_datetime(df["date"])
            daily_map[sym] = df.sort_values("date").reset_index(drop=True)
    return daily_map


def _component_name_map(components: pd.DataFrame) -> dict[str, str | None]:
    name_map = {}
    if "symbol" not in components.columns:
        return name_map
    for _, row in components.iterrows():
        sym = row.get("symbol")
        if not sym:
            continue
        name_map[str(sym)] = row.get("name")
    return name_map


def run_backtest(
    start: pd.Timestamp,
    end: pd.Timestamp,
    calendar,
    components: pd.DataFrame,
    fee: float,
    slippage: float,
    topn: int,
    rebalance_days: list[pd.Timestamp],
    index_df: pd.DataFrame,
    log_positions: bool = True,
    log_trades: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run monthly rebalance backtest with daily valuation."""
    start = pd.Timestamp(start)
    end = pd.Timestamp(end)
    trade_days = calendar.between(start, end)

    symbols = components["symbol"].dropna().unique().tolist() if "symbol" in components.columns else []
    daily_map = _load_daily(symbols)
    name_map = _component_name_map(components)

    cash = 1_000_000.0
    positions: dict[str, int] = {}
    nav_records: list[dict] = []
    positions_records: list[dict] = []
    trades_records: list[dict] = []

    for dt in trade_days:
        dt = pd.Timestamp(dt)
        day_trades = []

        if dt in rebalance_days:
            allow = hs300_trend_filter(index_df, dt)
            scores = rank_momentum(dt, components, daily_map) if allow else []
            score_map = {sym: score for sym, score in scores}
            rank_map = {sym: i + 1 for i, (sym, _) in enumerate(scores)}
            target_syms = [] if not allow else [s for s, _ in scores[:topn]]

            equity = cash
            for sym, qty in positions.items():
                df = daily_map.get(sym)
                if df is None or df.empty:
                    continue
                px = df[df["date"] <= dt].iloc[-1]["close"]
                equity += qty * float(px)

            target_weights = {sym: 1.0 / len(target_syms) for sym in target_syms} if target_syms else {}
            target_values = {sym: equity * w for sym, w in target_weights.items()}

            # Sell positions not in target
            for sym in list(positions.keys()):
                if sym not in target_values:
                    df = daily_map.get(sym)
                    if df is None or df.empty:
                        continue
                    px = df[df["date"] <= dt].iloc[-1]["close"]
                    sell_px = float(px) * (1 - slippage)
                    qty = int(positions[sym])
                    if qty <= 0:
                        continue
                    proceeds = qty * sell_px
                    fee_cost = proceeds * fee
                    cash += proceeds - fee_cost
                    positions.pop(sym, None)

                    reason = "trend_filter_off" if not allow else "rebalance"
                    if log_trades:
                        day_trades.append(
                            {
                                "date": dt,
                                "symbol": sym,
                                "side": "SELL",
                                "price": sell_px,
                                "shares": qty,
                                "gross_amount": proceeds,
                                "fee": fee_cost,
                                "net_amount": proceeds - fee_cost,
                                "target_weight": 0.0,
                                "reason": reason,
                                "momentum_value": score_map.get(sym, float("nan")),
                                "rank": rank_map.get(sym, pd.NA),
                                "turnover": 0.0,
                            }
                        )

            # Buy/adjust target positions
            for sym, tgt_val in target_values.items():
                df = daily_map.get(sym)
                if df is None or df.empty:
                    continue
                px = df[df["date"] <= dt].iloc[-1]["close"]
                buy_px = float(px) * (1 + slippage)
                cur_qty = positions.get(sym, 0)
                cur_val = cur_qty * buy_px
                diff_val = tgt_val - cur_val
                if diff_val <= 0:
                    continue
                # TODO: enforce 100-share lots if needed
                qty = int(diff_val / buy_px)
                if qty <= 0:
                    continue
                cost = qty * buy_px
                fee_cost = cost * fee
                if cash >= cost + fee_cost:
                    cash -= cost + fee_cost
                    positions[sym] = cur_qty + qty

                    if log_trades:
                        day_trades.append(
                            {
                                "date": dt,
                                "symbol": sym,
                                "side": "BUY",
                                "price": buy_px,
                                "shares": qty,
                                "gross_amount": cost,
                                "fee": fee_cost,
                                "net_amount": -(cost + fee_cost),
                                "target_weight": target_weights.get(sym, 0.0),
                                "reason": "rebalance",
                                "momentum_value": score_map.get(sym, float("nan")),
                                "rank": rank_map.get(sym, pd.NA),
                                "turnover": 0.0,
                            }
                        )

        # Daily valuation
        equity = cash
        position_rows = []
        for sym, qty in positions.items():
            df = daily_map.get(sym)
            if df is None or df.empty:
                continue
            px = df[df["date"] <= dt].iloc[-1]["close"]
            px = float(px)
            mv = qty * px
            equity += mv
            position_rows.append(
                {
                    "date": dt,
                    "symbol": sym,
                    "shares": int(qty),
                    "price": px,
                    "market_value": mv,
                    "weight": 0.0,
                    "total_equity": 0.0,
                    "cash": cash,
                    "name": name_map.get(sym),
                }
            )

        nav_records.append({"date": dt, "nav": equity})

        if log_positions and position_rows:
            for row in position_rows:
                row["total_equity"] = equity
                row["weight"] = row["market_value"] / equity if equity > 0 else 0.0
            positions_records.extend(position_rows)

        if log_trades and day_trades:
            total_trade_value = sum(abs(t["gross_amount"]) for t in day_trades)
            turnover = total_trade_value / equity if equity > 0 else 0.0
            for t in day_trades:
                t["turnover"] = turnover
            trades_records.extend(day_trades)

    nav = pd.DataFrame(nav_records).sort_values("date").reset_index(drop=True)

    positions_cols = [
        "date",
        "symbol",
        "shares",
        "price",
        "market_value",
        "weight",
        "total_equity",
        "cash",
        "name",
    ]
    trades_cols = [
        "date",
        "symbol",
        "side",
        "price",
        "shares",
        "gross_amount",
        "fee",
        "net_amount",
        "target_weight",
        "reason",
        "momentum_value",
        "rank",
        "turnover",
    ]

    if positions_records:
        positions_df = pd.DataFrame(positions_records)
        positions_df = positions_df[positions_cols]
        positions_df = positions_df.sort_values(["date", "symbol"]).reset_index(drop=True)
        positions_df = positions_df.drop_duplicates(subset=["date", "symbol"], keep="last")
    else:
        positions_df = pd.DataFrame(columns=positions_cols)

    if trades_records:
        trades_df = pd.DataFrame(trades_records)
        trades_df = trades_df[trades_cols]
        trades_df = trades_df.sort_values(["date", "symbol", "side"]).reset_index(drop=True)
        trades_df = trades_df.drop_duplicates(subset=["date", "symbol", "side"], keep="last")
    else:
        trades_df = pd.DataFrame(columns=trades_cols)

    return nav, positions_df, trades_df
