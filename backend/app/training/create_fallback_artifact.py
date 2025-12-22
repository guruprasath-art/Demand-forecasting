from __future__ import annotations

from pathlib import Path
import joblib

from app.data.bigquery_client import fetch_demand_with_context
from app.services.fallback_model import SimpleModel, SimpleEncoder


def create_artifact() -> Path:
    df = fetch_demand_with_context()
    if df.empty:
        raise RuntimeError("No data available from BigQuery to build fallback artifact.")

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
        "sku_encoder": SimpleEncoder(df),
        "history_df": df,
    }

    models_dir = Path(__file__).resolve().parent.parent / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    model_path = models_dir / "demand_model.joblib"
    joblib.dump(artifact, model_path)
    return model_path


def main():
    path = create_artifact()
    print(f"Created fallback artifact at: {path}")


if __name__ == "__main__":
    main()
