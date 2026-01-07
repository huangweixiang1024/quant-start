import argparse
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
from tqdm import tqdm

from src.config import DEFAULT_CONFIG, ENABLE_LOG_POSITIONS, ENABLE_LOG_TRADES, PROCESSED_DIR
from src.utils.io import ensure_dir
from src.data.fetch_index import fetch_index_hs300
from src.data.fetch_components import fetch_csi500_components
from src.data.fetch_daily import fetch_stock_daily
from src.data.calendar import TradingCalendar
from src.backtest.engine import run_backtest
from src.backtest.metrics import summarize_metrics
from src.data.store import (
    index_path,
    components_path,
    daily_path,
    nav_path,
    positions_path,
    trades_path,
    read_parquet,
    write_parquet,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="A-share minimal live prototype")
    parser.add_argument("--start", type=str, default=DEFAULT_CONFIG["start"])
    parser.add_argument("--end", type=str, default=DEFAULT_CONFIG["end"])
    parser.add_argument("--topn", type=int, default=DEFAULT_CONFIG["topn"])
    parser.add_argument("--fee", type=float, default=DEFAULT_CONFIG["fee"])
    parser.add_argument("--slippage", type=float, default=DEFAULT_CONFIG["slippage"])
    parser.add_argument("--refresh", action="store_true", help="Ignore cache and refetch data")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)

    t0 = time.perf_counter()
    ensure_dir(Path("data/raw"))
    ensure_dir(Path("data/raw/daily"))
    ensure_dir(Path(PROCESSED_DIR))

    print("[1/7] 拉取沪深300指数 / Fetch HS300 index")
    t1 = time.perf_counter()
    if args.refresh or not index_path().exists():
        index_df = fetch_index_hs300(start, end)
        write_parquet(index_df, index_path())
    else:
        index_df = read_parquet(index_path())
    print(
        f"HS300 行数 / rows: {len(index_df)}; "
        f"耗时 / elapsed: {time.perf_counter() - t1:.2f}s"
    )

    print("[2/7] 拉取中证500成分 / Fetch CSI500 components")
    t2 = time.perf_counter()
    if args.refresh or not components_path().exists():
        comp_df = fetch_csi500_components()
        write_parquet(comp_df, components_path())
    else:
        comp_df = read_parquet(components_path())
    print(
        f"成分股数量 / components: {comp_df['symbol'].nunique()}; "
        f"耗时 / elapsed: {time.perf_counter() - t2:.2f}s"
    )

    print("[3/7] 拉取成分股日线 / Fetch daily bars for components")
    t3 = time.perf_counter()
    symbols = comp_df["symbol"].dropna().unique().tolist()
    fetched_files = 0
    total_new_rows = 0
    for sym in tqdm(symbols, desc="daily", ncols=80):
        path = daily_path(sym)
        if args.refresh or not path.exists():
            df = fetch_stock_daily(sym, start, end)
            if df is not None and not df.empty:
                write_parquet(df, path)
                fetched_files += 1
                total_new_rows += len(df)
        else:
            df_old = read_parquet(path)
            df_new = fetch_stock_daily(sym, df_old["date"].max(), end)
            if df_new is not None and not df_new.empty:
                df = pd.concat([df_old, df_new], ignore_index=True)
                df = df.drop_duplicates(subset=["date"]).sort_values("date").reset_index(drop=True)
                write_parquet(df, path)
                fetched_files += 1
                total_new_rows += len(df_new)
    print(
        f"更新文件数 / files updated: {fetched_files}; "
        f"新增行数 / new rows: {total_new_rows}; "
        f"耗时 / elapsed: {time.perf_counter() - t3:.2f}s"
    )

    print("[4/7] 构建交易日历 / Build trading calendar")
    t4 = time.perf_counter()
    calendar = TradingCalendar(index_df)
    rebalance_days = calendar.month_first_trade_days(start, end)
    print(
        f"交易日数量 / trade days: {len(calendar.between(start, end))}; "
        f"调仓日数量 / rebalance days: {len(rebalance_days)}; "
        f"耗时 / elapsed: {time.perf_counter() - t4:.2f}s"
    )

    print("[5/7] 运行回测 / Run backtest")
    t5 = time.perf_counter()
    nav, positions_df, trades_df = run_backtest(
        start=start,
        end=end,
        calendar=calendar,
        components=comp_df,
        fee=args.fee,
        slippage=args.slippage,
        topn=args.topn,
        rebalance_days=rebalance_days,
        index_df=index_df,
        log_positions=ENABLE_LOG_POSITIONS,
        log_trades=ENABLE_LOG_TRADES,
    )
    print(
        f"NAV 行数 / nav rows: {len(nav)}; "
        f"耗时 / elapsed: {time.perf_counter() - t5:.2f}s"
    )

    print("[6/7] 保存净值 / Save NAV")
    t6 = time.perf_counter()
    write_parquet(nav, nav_path())
    print(f"保存完成 / saved; 耗时 / elapsed: {time.perf_counter() - t6:.2f}s")

    if ENABLE_LOG_POSITIONS:
        pos_path = positions_path()
        write_parquet(positions_df, pos_path)
        if len(positions_df) > 0:
            pos_min = positions_df["date"].min()
            pos_max = positions_df["date"].max()
            print(
                f"positions_daily 行数 / rows: {len(positions_df)}; "
                f"日期范围 / range: {pos_min} ~ {pos_max}"
            )
        else:
            print("positions_daily 行数 / rows: 0")

    if ENABLE_LOG_TRADES:
        tr_path = trades_path()
        write_parquet(trades_df, tr_path)
        if len(trades_df) > 0:
            tr_min = trades_df["date"].min()
            tr_max = trades_df["date"].max()
            print(
                f"trades 行数 / rows: {len(trades_df)}; "
                f"日期范围 / range: {tr_min} ~ {tr_max}"
            )
        else:
            print("trades 行数 / rows: 0")

    print("[7/7] 指标与绘图 / Metrics & plot")
    t7 = time.perf_counter()
    metrics = summarize_metrics(nav)
    for k, v in metrics.items():
        print(f"{k}: {v}")

    try:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 4))
        plt.plot(nav["date"], nav["nav"])
        plt.title("NAV Curve")
        plt.tight_layout()
        plt.show()
    except Exception as e:
        print(f"绘图失败 / plot failed: {e}")
    print(f"总耗时 / total elapsed: {time.perf_counter() - t0:.2f}s")


if __name__ == "__main__":
    main()
