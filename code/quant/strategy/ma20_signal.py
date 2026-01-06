import pandas as pd

def add_signals(df: pd.DataFrame, ma_window: int = 20) -> pd.DataFrame:
    df = df.copy()
    df["ma"] = df["close"].rolling(ma_window).mean()
    # 信号：收盘价 > MA 持有，否则空仓
    df["signal"] = (df["close"] > df["ma"]).astype(int)
    return df
