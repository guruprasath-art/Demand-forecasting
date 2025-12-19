import argparse
from pathlib import Path

import pandas as pd
import yaml


def load_config(config_path: Path) -> dict:
    with config_path.open("r") as f:
        return yaml.safe_load(f)


def ingest_csv_to_parquet(
    input_csv: Path,
    output_dir: Path,
    date_column: str,
) -> Path:
    """
    Load raw CSV and write to Parquet in a standardized format.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(input_csv)

    if date_column not in df.columns:
        raise ValueError(f"Expected date column '{date_column}' in input CSV.")

    df[date_column] = pd.to_datetime(df[date_column])
    df = df.sort_values(by=[date_column])

    output_path = output_dir / "sales.parquet"
    df.to_parquet(output_path, index=False)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Ingest raw CSV into Parquet format.")
    parser.add_argument(
        "--config",
        type=str,
        default="backend/configs/model.yaml",
        help="Path to YAML config file.",
    )
    parser.add_argument(
        "--input_csv",
        type=str,
        required=True,
        help="Path to input CSV file with raw sales data.",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    cfg = load_config(config_path)

    raw_dir = Path(cfg["paths"]["raw_data_dir"])
    processed_dir = Path(cfg["paths"]["processed_data_dir"])

    raw_dir.mkdir(parents=True, exist_ok=True)
    # Copy/standardize raw input to processed parquet
    input_csv_path = Path(args.input_csv)
    if not input_csv_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv_path}")

    # Store a copy of raw CSV under raw_data_dir for traceability
    raw_copy = raw_dir / input_csv_path.name
    if raw_copy.resolve() != input_csv_path.resolve():
        raw_copy.write_bytes(input_csv_path.read_bytes())

    output_parquet = ingest_csv_to_parquet(
        input_csv=input_csv_path,
        output_dir=processed_dir,
        date_column=cfg["data"]["date_column"],
    )

    print(f"Ingested data written to: {output_parquet}")


if __name__ == "__main__":
    main()


