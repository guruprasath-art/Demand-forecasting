from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import pandas as pd
import yaml


def load_config(config_path: Path) -> dict:
    with config_path.open("r") as f:
        return yaml.safe_load(f)


@dataclass
class TimeSplitResult:
    train: pd.DataFrame
    val: pd.DataFrame
    test: pd.DataFrame


def time_based_split(
    df: pd.DataFrame,
    date_column: str,
    test_days: int,
    val_days: int,
) -> TimeSplitResult:
    """
    Perform a strictly time-based split: [train | val | test] by days.
    """
    df = df.sort_values(by=[date_column])
    max_date = df[date_column].max()

    test_start = max_date - pd.Timedelta(days=test_days - 1)
    val_end = test_start - pd.Timedelta(days=1)
    val_start = val_end - pd.Timedelta(days=val_days - 1)

    train = df[df[date_column] < val_start].copy()
    val = df[(df[date_column] >= val_start) & (df[date_column] <= val_end)].copy()
    test = df[df[date_column] >= test_start].copy()

    return TimeSplitResult(train=train, val=val, test=test)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Time-based train/val/test split.")
    parser.add_argument(
        "--config",
        type=str,
        default="backend/configs/model.yaml",
        help="Path to YAML config file.",
    )
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    features_dir = Path(cfg["paths"]["features_data_dir"])
    date_col = cfg["data"]["date_column"]
    split_cfg = cfg["split"]

    features_path = features_dir / "features.parquet"
    if not features_path.exists():
        raise FileNotFoundError(
            f"Features parquet not found: {features_path}. Run features step first."
        )

    df = pd.read_parquet(features_path)
    df[date_col] = pd.to_datetime(df[date_col])

    split_result = time_based_split(
        df=df,
        date_column=date_col,
        test_days=split_cfg["test_days"],
        val_days=split_cfg["val_days"],
    )

    # Save each split
    split_dir = features_dir / "splits"
    split_dir.mkdir(parents=True, exist_ok=True)
    split_result.train.to_parquet(split_dir / "train.parquet", index=False)
    split_result.val.to_parquet(split_dir / "val.parquet", index=False)
    split_result.test.to_parquet(split_dir / "test.parquet", index=False)

    print(f"Train/val/test splits written to: {split_dir}")


if __name__ == "__main__":
    main()


