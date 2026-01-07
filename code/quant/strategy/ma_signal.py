import pandas as pd

def add_signals(df, ma_window: int):
    df = df.copy()
    df["ma"] = df["close"].rolling(ma_window).mean()
    df["signal"] = (df["close"] > df["ma"]).astype(int)
    return df
