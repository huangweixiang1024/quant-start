# A Share Quant Minimal Live Prototype

A minimal, reproducible daily-frequency backtest prototype for A-share stocks. It implements a CSI500 momentum rotation strategy with HS300 trend filter, using akshare data cached to Parquet.

## Features
- HS300 trend filter (close > 120-day MA)
- CSI500 components as fixed universe (no historical changes yet)
- Momentum factor (120-day return)
- Monthly rebalance on first trading day of each month
- Equal-weight portfolio, fees and slippage configurable
- Parquet cache with incremental daily updates
- Net asset value output and equity curve plot

## Install
```bash
python -m venv venv311
source venv311/bin/activate
pip install -r requirements.txt
```

## First-time data fetch
```bash
python main.py --start 2018-01-01 --end 2024-12-31
```

## Run backtest
```bash
python main.py --start 2018-01-01 --end 2024-12-31 --topn 10 --fee 0.0003 --slippage 0.0002
```

## Outputs
- NAV file: `data/processed/nav.parquet`
- Positions snapshot: `data/processed/positions_daily.parquet` (empty rows on cash-only days)
- Trades detail: `data/processed/trades.parquet`
- Equity curve: matplotlib window
- Metrics printed to console

## Output file schema
- `nav.parquet`: date, nav
- `positions_daily.parquet`: date, symbol, shares, price, market_value, weight, total_equity, cash, name
- `trades.parquet`: date, symbol, side, price, shares, gross_amount, fee, net_amount, target_weight, reason, momentum_value, rank, turnover

## Audit checks
```bash
python -m src.utils.audit --tol 0.05
```

## Cache cleanup
```bash
rm -rf data/raw data/processed
```

## FAQ
- akshare failed / rate limited
  - Try again later, or set `--refresh` to refetch.
  - Some endpoints may change; see `src/data/fetch_*.py` adapters.
- Network issues
  - Ensure your network can access data sources and avoid frequent retries.
- Missing data or empty results
  - Some symbols may be delisted or have short history. The engine skips them.
