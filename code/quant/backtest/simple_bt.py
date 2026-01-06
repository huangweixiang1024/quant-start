import pandas as pd

def backtest_one_asset(
    df: pd.DataFrame,
    fee_rate: float = 0.0003,     # 手续费（示例：万3）
    slippage: float = 0.0010,     # 滑点（示例：千1）
    init_cash: float = 100_000.0  # 初始资金
) -> dict:
    df = df.copy().reset_index(drop=True)

    # 用“前一天的 signal”决定“今天开盘”是否持有
    df["pos"] = df["signal"].shift(1).fillna(0).astype(int)

    cash = init_cash
    shares = 0.0
    equity_curve = []
    trades = []

    for i in range(len(df)):
        date = df.loc[i, "date"]
        open_px = float(df.loc[i, "open"])
        close_px = float(df.loc[i, "close"])
        target_pos = int(df.loc[i, "pos"])  # 0/1

        # 当前持仓市值（用开盘价做交易决策点）
        current_value = shares * open_px
        current_equity = cash + current_value

        # 目标：满仓 or 空仓（极简）
        if target_pos == 1 and shares == 0:
            # 买入：用全部现金买
            buy_px = open_px * (1 + slippage)
            qty = cash / (buy_px * (1 + fee_rate))
            cost = qty * buy_px
            fee = cost * fee_rate
            cash = cash - cost - fee
            shares = qty
            trades.append({"date": date, "action": "BUY", "price": buy_px, "qty": qty, "fee": fee})

        elif target_pos == 0 and shares > 0:
            # 卖出：卖光
            sell_px = open_px * (1 - slippage)
            proceeds = shares * sell_px
            fee = proceeds * fee_rate
            cash = cash + proceeds - fee
            trades.append({"date": date, "action": "SELL", "price": sell_px, "qty": shares, "fee": fee})
            shares = 0.0

        # 收盘记净值（也可以用收盘价计算权益）
        equity = cash + shares * close_px
        equity_curve.append({"date": date, "equity": equity})

    eq = pd.DataFrame(equity_curve).set_index("date")
    tr = pd.DataFrame(trades)

    # 指标
    eq["ret"] = eq["equity"].pct_change().fillna(0)
    ann = (1 + eq["ret"]).prod() ** (252 / max(1, len(eq))) - 1
    vol = eq["ret"].std() * (252 ** 0.5)
    sharpe = (eq["ret"].mean() / (eq["ret"].std() + 1e-12)) * (252 ** 0.5)

    roll_max = eq["equity"].cummax()
    dd = eq["equity"] / roll_max - 1
    mdd = dd.min()

    return {
        "equity": eq,
        "trades": tr,
        "metrics": {
            "ann_return": float(ann),
            "ann_vol": float(vol),
            "sharpe": float(sharpe),
            "max_drawdown": float(mdd),
            "num_trades": int(len(tr)),
        },
    }
