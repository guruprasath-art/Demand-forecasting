from __future__ import annotations

from datetime import timedelta
from functools import lru_cache
from pathlib import Path
from typing import List

import joblib
import numpy as np
import pandas as pd


MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "demand_model.joblib"


@lru_cache(maxsize=1)
def load_artifact() -> dict:
    # Prefer the trained artifact if present, but be resilient: if the
    # artifact requires unavailable packages (e.g. scikit-learn) we build
    # a minimal runtime artifact so the API remains usable for demos.
    if MODEL_PATH.exists():
        try:
            return joblib.load(MODEL_PATH)
        except ModuleNotFoundError:
            # Fall through to create a lightweight artifact
            pass

    # Fallback: construct a simple artifact using historical data
    # Prefer live BigQuery-backed data if available, otherwise fall back
    # to the offline parquet features (if present).
    try:
        from app.data.bigquery_client import fetch_demand_with_context

        history_df = fetch_demand_with_context()
        if history_df.empty:
            raise RuntimeError("BigQuery returned no history")
    except Exception:
        from app.data_loader import load_history_df

        history_df = load_history_df()

    class SimpleModel:
        def predict(self, X):
            # Predict using the last observed value for the SKU if available,
            # otherwise return zero. X shape: (n_samples, n_features)
            try:
                last = float(history_df["total_quantity"].dropna().values[-1])
            except Exception:
                last = 0.0
            return [last for _ in range(len(X))]

    class SimpleEncoder:
        def __init__(self, df):
            uniq = list(df["sku"].astype(str).unique()) if "sku" in df.columns else []
            self._map = {s: i for i, s in enumerate(uniq)}

        def transform(self, items):
            return [self._map.get(str(i), 0) for i in items]

    feature_cols = [
        "sku_encoded",
        "day_of_week",
        "month",
        "lag_7",
        "rolling_mean_14",
        "event_count",
        "active_users",
        "price",
    ]

    artifact = {
        "model": SimpleModel(),
        "feature_cols": feature_cols,
        "sku_encoder": SimpleEncoder(history_df),
        "history_df": history_df,
        "_fallback": True,
    }
    return artifact


def list_skus() -> List[str]:
    artifact = load_artifact()
    history_df: pd.DataFrame = artifact["history_df"]
    skus = sorted(history_df["sku"].astype(str).unique())
    return skus


def _iterative_forecast_for_sku(sku: str, horizon: int) -> pd.DataFrame:
    artifact = load_artifact()
    model = artifact["model"]
    feature_cols: List[str] = artifact["feature_cols"]
    history_df: pd.DataFrame = artifact["history_df"].copy()
    le = artifact["sku_encoder"]

    history_df["date"] = pd.to_datetime(history_df["date"])
    sku_history = history_df[history_df["sku"] == sku].sort_values("date")
    if sku_history.empty:
        raise ValueError(f"No history found for SKU '{sku}'.")

    encoded_sku = int(le.transform([sku])[0])

    # Maintain recent target history for lag/rolling computation
    recent_targets: List[float] = list(
        sku_history["total_quantity"].astype(float).values
    )

    last_date = sku_history["date"].max()
    forecasts: List[dict] = []

    # Derive which lags and rolling windows exist from feature_cols
    lags: List[int] = []
    rolling_windows: List[int] = []
    for col in feature_cols:
        if col.startswith("lag_"):
            lags.append(int(col.split("_", 1)[1]))
        elif col.startswith("rolling_mean_"):
            rolling_windows.append(int(col.split("_", 2)[2]))

    max_lag = max(lags + rolling_windows) if (lags or rolling_windows) else 0
    if max_lag > 0 and len(recent_targets) < max_lag:
        # If history is very short, pad with the first observed value
        first_val = recent_targets[0]
        while len(recent_targets) < max_lag:
            recent_targets.insert(0, first_val)

    # Capture latest context features for this SKU/date to reuse in the future horizon
    latest_row = sku_history.sort_values("date").iloc[-1]
    context_defaults: dict = {}
    for col in ["event_count", "active_users", "price", "product_category_encoded"]:
        if col in sku_history.columns:
            context_defaults[col] = float(latest_row[col])

    for step in range(1, horizon + 1):
        forecast_date = last_date + timedelta(days=step)

        row: dict = {
            "sku_encoded": encoded_sku,
            "day_of_week": int(forecast_date.weekday()),
            "month": int(forecast_date.month),
        }

        # Numeric context features: keep last observed value
        for ctx_col, value in context_defaults.items():
            row[ctx_col] = value

        for lag in lags:
            row[f"lag_{lag}"] = float(recent_targets[-lag])

        for window in rolling_windows:
            window_vals = recent_targets[-window:]
            row[f"rolling_mean_{window}"] = float(np.mean(window_vals))

        # Build feature matrix defensively: if a feature is missing from the
        # constructed `row` (e.g. encoded categorical features), fill with 0.0
        # so the model / fallback logic can continue without raising KeyError.
        X = np.array([[row.get(c, 0.0) for c in feature_cols]])

        # If we are using the fallback artifact, produce forecasts using a
        # simple exponential smoothing over recent_targets rather than
        # calling a missing/full ML model. This avoids depending on
        # scikit-learn when it's not installed.
        if artifact.get("_fallback", False):
            # Simple exponential smoothing: alpha-weighted average with alpha=0.3
            alpha = 0.3
            if len(recent_targets) == 0:
                y_pred = 0.0
            else:
                s = recent_targets[-1]
                # apply smoothing over the last up to 7 points
                for val in recent_targets[-7:][::-1]:
                    s = alpha * val + (1 - alpha) * s
                y_pred = float(s)
        else:
            y_pred = float(model.predict(X)[0])
        recent_targets.append(y_pred)

        forecasts.append(
            {
                "date": forecast_date,
                "sku": sku,
                "forecast": y_pred,
            }
        )

    return pd.DataFrame(forecasts)


def forecast_sku(sku: str, horizon: int) -> pd.DataFrame:
    """
    Public entry point used by FastAPI layer.
    """
    return _iterative_forecast_for_sku(sku, horizon=horizon)


