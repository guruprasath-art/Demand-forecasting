from pathlib import Path

import pandas as pd
import yaml


def load_config(config_path: Path) -> dict:
    with config_path.open("r") as f:
        return yaml.safe_load(f)


def build_features(
    input_parquet: Path,
    output_dir: Path,
    date_column: str,
    sku_column: str,
    target_column: str,
    lags: list[int],
    rolling_mean_windows: list[int],
) -> Path:
    """
    Create lag and rolling mean features per-SKU and write to Parquet.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(input_parquet)
    df[date_column] = pd.to_datetime(df[date_column])

    df = df.sort_values(by=[sku_column, date_column])

    # Generate lag features
    for lag in lags:
        df[f"{target_column}_lag_{lag}"] = df.groupby(sku_column)[target_column].shift(
            lag
        )

    # Generate rolling mean features
    for window in rolling_mean_windows:
        df[f"{target_column}_rolling_mean_{window}"] = (
            df.groupby(sku_column)[target_column]
            .shift(1)
            .rolling(window=window)
            .mean()
        )

    output_path = output_dir / "features.parquet"
    df.to_parquet(output_path, index=False)
    return output_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Build lag and rolling features.")
    parser.add_argument(
        "--config",
        type=str,
        default="backend/configs/model.yaml",
        help="Path to YAML config file.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = load_config(config_path)

    processed_dir = Path(cfg["paths"]["processed_data_dir"])
    features_dir = Path(cfg["paths"]["features_data_dir"])
    date_col = cfg["data"]["date_column"]
    sku_col = cfg["data"]["sku_column"]
    target_col = cfg["data"]["target_column"]
    lags = cfg["features"]["lags"]
    rolling_windows = cfg["features"]["rolling_mean_windows"]

    input_parquet = processed_dir / "sales.parquet"
    if not input_parquet.exists():
        raise FileNotFoundError(
            f"Processed parquet not found: {input_parquet}. Run ingest first."
        )

    output_path = build_features(
        input_parquet=input_parquet,
        output_dir=features_dir,
        date_column=date_col,
        sku_column=sku_col,
        target_column=target_col,
        lags=lags,
        rolling_mean_windows=rolling_windows,
    )

    print(f"Feature data written to: {output_path}")


if __name__ == "__main__":
    main()


