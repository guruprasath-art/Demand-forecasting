from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd

from .data_loader import load_config, load_history_df


@lru_cache(maxsize=1)
def load_model_artifact() -> Dict:
    """
    Load the tuned model if present, otherwise fall back to the normal model.
    """
    cfg = load_config()
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
    sku: str,
    horizon: int,
) -> pd.DataFrame:
    """
    Run an autoregressive forecasting loop for a single SKU, using the
    same feature structure (lags + rolling means) as the training pipeline.
    """
    cfg = load_config()
    artifact = load_model_artifact()
    history_df = load_history_df()

    date_col = cfg["data"]["date_column"]
    sku_col = cfg["data"]["sku_column"]
    target_col = cfg["data"]["target_column"]
    extra_features: List[str] = cfg["data"].get("extra_feature_columns", [])

    lags: List[int] = cfg["features"]["lags"]
    rolling_windows: List[int] = cfg["features"]["rolling_mean_windows"]

    sku_history = history_df[history_df[sku_col] == sku].copy()
    if sku_history.empty:
        raise ValueError(f"No history found for SKU '{sku}'.")

    sku_history = sku_history.sort_values(by=[date_col])
    last_date = sku_history[date_col].max()
    last_row = sku_history.iloc[-1].copy()

    le = artifact["sku_label_encoder"]
    encoded_sku = le.transform([sku])[0]

    recent_targets = list(
        sku_history.sort_values(by=[date_col])[target_col].values[
            -max(lags + rolling_windows) :
        ]
    )

    future_records: List[Dict] = []
    feature_cols: List[str] = artifact["feature_cols"]
    model = artifact["model"]

    for step in range(1, horizon + 1):
        forecast_date = last_date + timedelta(days=step)

        feature_row: Dict = {}
        for col in extra_features:
            feature_row[col] = last_row[col]

        feature_row[sku_col] = encoded_sku

        for lag in lags:
            feature_row[f"{target_col}_lag_{lag}"] = recent_targets[-lag]

        for window in rolling_windows:
            if len(recent_targets) >= window:
                feature_row[f"{target_col}_rolling_mean_{window}"] = float(
                    np.mean(recent_targets[-window:])
                )
            else:
                feature_row[f"{target_col}_rolling_mean_{window}"] = float(
                    np.mean(recent_targets)
                )

        X_input = np.array([[feature_row[col] for col in feature_cols]])
        y_pred = float(model.predict(X_input)[0])

        recent_targets.append(y_pred)
        future_records.append(
            {
                date_col: forecast_date,
                sku_col: sku,
                "forecast": y_pred,
            }
        )

    return pd.DataFrame(future_records)


