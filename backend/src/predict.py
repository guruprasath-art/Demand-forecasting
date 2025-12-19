from datetime import timedelta
from pathlib import Path
from typing import List

import joblib
import numpy as np
import pandas as pd
import yaml


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


def iterative_forecast_for_sku(
    history_df: pd.DataFrame,
    sku: str,
    artifact: dict,
    cfg: dict,
    horizon: int,
) -> pd.DataFrame:
    """
    Simple autoregressive forecasting loop using lag/rolling features.
    Assumes exogenous variables (price, promo) remain constant at last observed values.
    """
    date_col = cfg["data"]["date_column"]
    sku_col = cfg["data"]["sku_column"]
    target_col = cfg["data"]["target_column"]
    extra_features = cfg["data"].get("extra_feature_columns", [])

    lags: List[int] = cfg["features"]["lags"]
    rolling_windows: List[int] = cfg["features"]["rolling_mean_windows"]

    sku_history = history_df[history_df[sku_col] == sku].copy()
    if sku_history.empty:
        raise ValueError(f"No history found for SKU '{sku}'.")

    sku_history[date_col] = pd.to_datetime(sku_history[date_col])
    sku_history = sku_history.sort_values(by=[date_col])

    last_date = sku_history[date_col].max()
    last_row = sku_history.iloc[-1].copy()

    # Use label encoder from artifact
    le = artifact["sku_label_encoder"]
    encoded_sku = le.transform([sku])[0]

    # Keep a list of synthetic future rows
    future_records = []

    # Maintain rolling window of recent target values for computing lags/rolling
    recent_targets = list(
        sku_history.sort_values(by=[date_col])[target_col].values[-max(lags + rolling_windows) :]
    )

    for step in range(1, horizon + 1):
        forecast_date = last_date + timedelta(days=step)

        # Build feature row
        feature_row = {}
        # Exogenous variables: hold last observed values
        for col in extra_features:
            feature_row[col] = last_row[col]

        feature_row[sku_col] = encoded_sku

        # Compute lags based on recent_targets (which include previous forecasts)
        for lag in lags:
            feature_row[f"{target_col}_lag_{lag}"] = recent_targets[-lag]

        # Rolling means
        for window in rolling_windows:
            if len(recent_targets) >= window:
                feature_row[f"{target_col}_rolling_mean_{window}"] = float(
                    np.mean(recent_targets[-window:])
                )
            else:
                feature_row[f"{target_col}_rolling_mean_{window}"] = float(
                    np.mean(recent_targets)
                )

        feature_cols = artifact["feature_cols"]
        X_input = np.array([[feature_row[col] for col in feature_cols]])

        model = artifact["model"]
        y_pred = float(model.predict(X_input)[0])

        # Append prediction to recent_targets for next step
        recent_targets.append(y_pred)

        future_records.append(
            {
                date_col: forecast_date,
                sku_col: sku,
                "forecast": y_pred,
            }
        )

    return pd.DataFrame(future_records)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Batch prediction for all SKUs.")
    parser.add_argument(
        "--config",
        type=str,
        default="backend/configs/model.yaml",
        help="Path to YAML config file.",
    )
    parser.add_argument(
        "--horizon",
        type=int,
        default=14,
        help="Forecast horizon in days.",
    )
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    features_dir = Path(cfg["paths"]["features_data_dir"])
    forecast_dir = Path(cfg["paths"]["forecast_output_dir"])
    date_col = cfg["data"]["date_column"]
    sku_col = cfg["data"]["sku_column"]

    features_path = features_dir / "features.parquet"
    if not features_path.exists():
        raise FileNotFoundError(
            f"Features parquet not found: {features_path}. Run features step first."
        )

    history_df = pd.read_parquet(features_path)
    history_df[date_col] = pd.to_datetime(history_df[date_col])

    artifact = load_model_artifact(cfg)

    forecast_dir.mkdir(parents=True, exist_ok=True)

    all_skus = sorted(history_df[sku_col].unique())
    all_forecasts = []
    for sku in all_skus:
        sku_forecast = iterative_forecast_for_sku(
            history_df=history_df,
            sku=sku,
            artifact=artifact,
            cfg=cfg,
            horizon=args.horizon,
        )
        all_forecasts.append(sku_forecast)

    result_df = pd.concat(all_forecasts, ignore_index=True)
    output_path = forecast_dir / f"forecasts_h{args.horizon}.parquet"
    result_df.to_parquet(output_path, index=False)

    print(f"Batch forecasts for all SKUs written to: {output_path}")


if __name__ == "__main__":
    main()


