from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.preprocessing import LabelEncoder

from app.data.bigquery_client import fetch_demand_with_context
from app.features.feature_engineering import build_time_series_features


@dataclass
class TrainConfig:
    val_days: int = 30
    random_state: int = 42
    num_boost_round: int = 500
    early_stopping_rounds: int = 50


def time_based_train_val_split(df: pd.DataFrame, val_days: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.sort_values("date")
    max_date = df["date"].max()
    val_start = max_date - timedelta(days=val_days - 1)
    train = df[df["date"] < val_start].copy()
    val = df[df["date"] >= val_start].copy()
    return train, val


def prepare_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray, list[str], LabelEncoder]:
    """
    Build the feature matrix from the enriched feature frame.

    Uses:
      - sku_encoded
      - calendar features
      - lag and rolling features
      - numeric context features (event_count, active_users, price)
      - optional product_category encoding
    """
    df = df.dropna(subset=["total_quantity"]).copy()

    le = LabelEncoder()
    df["sku_encoded"] = le.fit_transform(df["sku"].astype(str))

    feature_cols: list[str] = ["sku_encoded", "day_of_week", "month"]

    # Context numeric features if present
    for col in ["event_count", "active_users", "price"]:
        if col in df.columns:
            df[col] = df[col].fillna(0.0).astype(float)
            feature_cols.append(col)

    # Optional categorical product_category
    if "product_category" in df.columns:
        cat_le = LabelEncoder()
        df["product_category_encoded"] = cat_le.fit_transform(
            df["product_category"].astype(str)
        )
        feature_cols.append("product_category_encoded")

    # All lag and rolling features
    feature_cols.extend(
        [c for c in df.columns if c.startswith("lag_") or c.startswith("rolling_mean_")]
    )

    X = df[feature_cols].copy()
    y = df["total_quantity"].astype(float).to_numpy()
    return X, y, feature_cols, le


def train_model(cfg: TrainConfig) -> Path:
    raw_df = fetch_demand_with_context()
    if raw_df.empty:
        raise RuntimeError("No data returned from BigQuery 'orders' table.")

    history_df = raw_df.copy()
    features_df = build_time_series_features(history_df)

    train_df, val_df = time_based_train_val_split(features_df, cfg.val_days)

    X_train, y_train, feature_cols, le = prepare_xy(train_df)
    X_val, y_val, _, _ = prepare_xy(val_df)

    model = LGBMRegressor(
        n_estimators=cfg.num_boost_round,
        random_state=cfg.random_state,
        objective="regression",
    )
    # LightGBM sklearn API in this version does not accept early_stopping_rounds directly;
    # rely on n_estimators and validation to tune capacity offline.
    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="l2",
    )

    val_pred = model.predict(X_val)
    val_mae = mean_absolute_error(y_val, val_pred)

    artifact = {
        "model": model,
        "feature_cols": feature_cols,
        "sku_encoder": le,
        "history_df": history_df,  # used for forecasting bootstrap
        "val_mae": float(val_mae),
    }

    models_dir = Path("backend/app/models")
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / "demand_model.joblib"
    joblib.dump(artifact, model_path)
    return model_path


def main() -> None:
    cfg = TrainConfig()
    model_path = train_model(cfg)
    print(f"Trained demand model saved to: {model_path}")


if __name__ == "__main__":
    main()


