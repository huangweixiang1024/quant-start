import pandas as pd
from strategy.ma_signal import add_signals
from backtest.simple_bt import backtest_one_asset

df = pd.read_csv("data/510300.csv")
df["date"] = pd.to_datetime(df["date"])

results = []

for ma in [5, 10, 20, 30, 60, 120]:
    df_sig = add_signals(df, ma_window=ma)
    res = backtest_one_asset(df_sig)

    metrics = res["metrics"]
    metrics["ma"] = ma
    results.append(metrics)

out = pd.DataFrame(results)
print(out.sort_values("ann_return", ascending=False))
