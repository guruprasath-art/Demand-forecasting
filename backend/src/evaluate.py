import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import yaml
from sklearn.metrics import mean_absolute_error, mean_squared_error


def load_config(config_path: Path) -> dict:
    with config_path.open("r") as f:
        return yaml.safe_load(f)


def load_model_artifact(cfg: dict) -> dict:
    tuned_model_dir = Path(cfg["paths"]["tuned_model_dir"])
    normal_model_dir = Path(cfg["paths"]["normal_model_dir"])

    tuned_model_path = tuned_model_dir / "model_tuned.joblib"
    normal_model_path = normal_model_dir / "model.joblib"

    if tuned_model_path.exists():
        return joblib.load(tuned_model_path)
    if normal_model_path.exists():
        return joblib.load(normal_model_path)

    raise FileNotFoundError("No trained model artifact found (normal or tuned).")


def evaluate_model_on_test(
    artifact: dict,
    test_df: pd.DataFrame,
    cfg: dict,
) -> dict:
    target_col = cfg["data"]["target_column"]
    date_col = cfg["data"]["date_column"]
    sku_col = cfg["data"]["sku_column"]

    df = test_df.dropna().copy()

    # Recreate SKU encoding
    le = artifact["sku_label_encoder"]
    df[sku_col] = le.transform(df[sku_col].astype(str))

    feature_cols = artifact["feature_cols"]
    X_test = df[feature_cols]
    y_true = df[target_col].values.astype(float)

    model = artifact["model"]
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))

    return {
        "MAE": mae,
        "RMSE": rmse,
        "n_samples": int(len(y_true)),
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate model on test split.")
    parser.add_argument(
        "--config",
        type=str,
        default="backend/configs/model.yaml",
        help="Path to YAML config file.",
    )
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    features_dir = Path(cfg["paths"]["features_data_dir"])
    metrics_dir = Path(cfg["paths"]["metrics_dir"])
    date_col = cfg["data"]["date_column"]

    split_dir = features_dir / "splits"
    test_path = split_dir / "test.parquet"
    if not test_path.exists():
        raise FileNotFoundError(
            "Test split not found. Run split.py and ensure test.parquet exists."
        )

    test_df = pd.read_parquet(test_path)
    test_df[date_col] = pd.to_datetime(test_df[date_col])

    artifact = load_model_artifact(cfg)
    metrics = evaluate_model_on_test(artifact, test_df, cfg)

    metrics_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = metrics_dir / "metrics.json"
    with metrics_path.open("w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics written to: {metrics_path}")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()


