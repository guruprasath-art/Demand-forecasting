from functools import lru_cache
from pathlib import Path
from typing import List

import pandas as pd
import yaml


BASE_DIR = Path(__file__).resolve().parent.parent

@lru_cache(maxsize=1)
def load_config(config_path: str = None) -> dict:
    if config_path is None:
        path = BASE_DIR / "configs" / "model.yaml"
    else:
        path = Path(config_path)
    with path.open("r") as f:
        return yaml.safe_load(f)


@lru_cache(maxsize=1)
def load_history_df() -> pd.DataFrame:
    """
    Load the full feature dataset used for training.
    This is used as historical context for forecasting and SKU discovery.
    """
    cfg = load_config()
    features_dir = Path(cfg["paths"]["features_data_dir"])
    features_path = features_dir / "features.parquet"
    if not features_path.exists():
        raise FileNotFoundError(
            f"Features parquet not found at {features_path}. "
            "Run the offline pipeline (ingest -> features -> split -> train) first."
        )

    date_col = cfg["data"]["date_column"]
    df = pd.read_parquet(features_path)
    df[date_col] = pd.to_datetime(df[date_col])
    return df


def list_skus() -> List[str]:
    cfg = load_config()
    sku_col = cfg["data"]["sku_column"]
    df = load_history_df()
    skus = sorted(df[sku_col].dropna().astype(str).unique())
    return skus


