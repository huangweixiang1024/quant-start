import pandas as pd

from strategy.ma_signal import add_signals
from backtest.simple_bt import backtest_one_asset


def run_one(df, ma: int):
    df_sig = add_signals(df, ma_window=ma)
    res = backtest_one_asset(df_sig)
    m = res["metrics"].copy()
    m["ma"] = ma
    return m


def main():
    df = pd.read_csv("data/510300.csv")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)

    # ---- 时间切分：前 70% 训练，后 30% 测试 ----
    split_idx = int(len(df) * 0.7)
    train = df.iloc[:split_idx].copy()
    test = df.iloc[split_idx:].copy()

    mas = list(range(20, 201, 5))

    # ---- 1) 样本内扫参 ----
    rows = [run_one(train, ma) for ma in mas]
    train_out = pd.DataFrame(rows).sort_values("ma").reset_index(drop=True)
    train_out.to_csv("experiments/train_metrics.csv", index=False)

    # 你可以在这里加硬约束：比如回撤不能小于 -0.45
    dd_limit = -0.45
    candidates = train_out[train_out["max_drawdown"] >= dd_limit].copy()
    if len(candidates) == 0:
        candidates = train_out.copy()

    best = candidates.sort_values("sharpe", ascending=False).iloc[0]
    best_ma = int(best["ma"])

    print("=== In-sample (TRAIN) best MA by Sharpe (with dd_limit) ===")
    print(best[["ma","ann_return","ann_vol","sharpe","max_drawdown","num_trades"]])

    # ---- 2) 样本外验证：锁死 best_ma ----
    test_m = run_one(test, best_ma)
    test_out = pd.DataFrame([test_m])
    test_out.to_csv("experiments/test_metrics.csv", index=False)

    print("\n=== Out-of-sample (TEST) using fixed MA =", best_ma, "===")
    print(test_out[["ma","ann_return","ann_vol","sharpe","max_drawdown","num_trades"]])

    print("\nSaved:")
    print(" - experiments/train_metrics.csv")
    print(" - experiments/test_metrics.csv")


if __name__ == "__main__":
    main()