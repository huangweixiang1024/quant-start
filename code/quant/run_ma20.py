import pandas as pd
import matplotlib.pyplot as plt

from strategy.ma20_signal import add_signals
from backtest.simple_bt import backtest_one_asset

df = pd.read_csv("data/510300.csv")
df["date"] = pd.to_datetime(df["date"])

df = add_signals(df, ma_window=20)
res = backtest_one_asset(df, fee_rate=0.0003, slippage=0.001, init_cash=100_000)

print("=== Metrics ===")
for k, v in res["metrics"].items():
    print(k, ":", v)

# 保存交易记录
res["trades"].to_csv("result_trades.csv", index=False)
print("saved trades -> result_trades.csv")

# 画净值曲线
eq = res["equity"]
plt.figure(figsize=(10,4))
plt.plot(eq.index, eq["equity"])
plt.title("Equity Curve (510300 MA20)")
plt.tight_layout()
plt.show()
