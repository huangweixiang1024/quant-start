import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import akshare as ak

print("numpy:", np.__version__)
print("pandas:", pd.__version__)

df = ak.fund_etf_hist_em(symbol="510300", period="daily", adjust="qfq")
print(df.head())

plt.plot(df["收盘"])
plt.title("510300 ETF")
plt.show()
