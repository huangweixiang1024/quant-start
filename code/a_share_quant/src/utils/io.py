"""IO helpers for parquet and directories."""

from pathlib import Path
import pandas as pd


def ensure_dir(path: Path) -> None:
    """Create directory if missing."""
    path.mkdir(parents=True, exist_ok=True)


def read_parquet(path: Path) -> pd.DataFrame:
    """Read parquet with engine fallback."""
    try:
        return pd.read_parquet(path, engine="pyarrow")
    except Exception:
        return pd.read_parquet(path, engine="fastparquet")


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    """Write parquet with engine fallback."""
    try:
        df.to_parquet(path, index=False, engine="pyarrow")
    except Exception:
        df.to_parquet(path, index=False, engine="fastparquet")
