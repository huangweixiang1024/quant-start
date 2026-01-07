import pandas as pd
import matplotlib.pyplot as plt

from strategy.ma_signal import add_signals
from backtest.simple_bt import backtest_one_asset


def main():
    df = pd.read_csv("data/510300.csv")
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])

    mas = list(range(20, 201, 5))
    rows = []

    for ma in mas:
        df_sig = add_signals(df, ma_window=ma)
        res = backtest_one_asset(df_sig)
        m = res["metrics"].copy()
        m["ma"] = ma
        rows.append(m)

    out = pd.DataFrame(rows).sort_values("ma").reset_index(drop=True)
    out.to_csv("experiments/ma_sweep_metrics.csv", index=False)

    print(out[["ma", "ann_return", "ann_vol", "sharpe", "max_drawdown", "num_trades"]])

    # ---- plots ----
    plt.figure()
    plt.plot(out["ma"], out["sharpe"], marker="o")
    plt.xlabel("MA window")
    plt.ylabel("Sharpe")
    plt.title("MA vs Sharpe")
    plt.grid(True)
    plt.show()

    plt.figure()
    plt.plot(out["ma"], out["max_drawdown"], marker="o")
    plt.xlabel("MA window")
    plt.ylabel("Max Drawdown")
    plt.title("MA vs Max Drawdown")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
