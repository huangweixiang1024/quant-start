"""Project configuration defaults."""

from datetime import datetime

DEFAULT_CONFIG = {
    "start": "2018-01-01",
    "end": datetime.now().strftime("%Y-%m-%d"),
    "topn": 10,
    "fee": 0.0003,
    "slippage": 0.0002,
}

ENABLE_LOG_POSITIONS = True
ENABLE_LOG_TRADES = True
PROCESSED_DIR = "data/processed"
