from pathlib import Path
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
import yaml
from lightgbm import LGBMRegressor
from sklearn.preprocessing import LabelEncoder


def load_config(config_path: Path) -> dict:
    with config_path.open("r") as f:
        return yaml.safe_load(f)


def prepare_xy(
    df: pd.DataFrame,
    cfg: dict,
) -> Tuple[pd.DataFrame, np.ndarray, list[str]]:
    target_col = cfg["data"]["target_column"]
    date_col = cfg["data"]["date_column"]
    sku_col = cfg["data"]["sku_column"]
    extra_features = cfg["data"].get("extra_feature_columns", [])

    # Drop rows with NaNs introduced by lags/rolling
    df = df.dropna().copy()

    # Encode SKU as categorical integer
    sku_le = LabelEncoder()
    df[sku_col] = sku_le.fit_transform(df[sku_col].astype(str))

    feature_cols: list[str] = []
    feature_cols.extend(extra_features)
    feature_cols.append(sku_col)

    # Add all lag/rolling columns automatically
    for col in df.columns:
        if col.startswith(f"{target_col}_lag_") or col.startswith(
            f"{target_col}_rolling_mean_"
        ):
            feature_cols.append(col)

    # Ensure we don't leak the target or date into features
    feature_cols = [c for c in feature_cols if c not in {target_col, date_col}]

    X = df[feature_cols].copy()
    y = df[target_col].values.astype(float)
    return X, y, feature_cols, sku_le


def train_model(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    cfg: dict,
    model_dir: Path,
) -> Path:
    model_dir.mkdir(parents=True, exist_ok=True)

    X_train, y_train, feature_cols, sku_le = prepare_xy(train_df, cfg)
    X_val, y_val, _, _ = prepare_xy(val_df, cfg)

    train_cfg = cfg["training"]
    random_state = train_cfg.get("random_state", 42)
    num_boost_round = train_cfg.get("num_boost_round", 1000)
    early_stopping_rounds = train_cfg.get("early_stopping_rounds", 50)

    model = LGBMRegressor(
        n_estimators=num_boost_round,
        random_state=random_state,
        objective="regression",
    )

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="l2",
        callbacks=None,
        early_stopping_rounds=early_stopping_rounds,
    )

    artifact = {
        "model": model,
        "feature_cols": feature_cols,
        "sku_label_encoder": sku_le,
        "config": cfg,
    }
    model_path = model_dir / "model.joblib"
    joblib.dump(artifact, model_path)
    return model_path


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Train LightGBM model.")
    parser.add_argument(
        "--config",
        type=str,
        default="backend/configs/model.yaml",
        help="Path to YAML config file.",
    )
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    features_dir = Path(cfg["paths"]["features_data_dir"])
    normal_model_dir = Path(cfg["paths"]["normal_model_dir"])
    date_col = cfg["data"]["date_column"]

    split_dir = features_dir / "splits"
    train_path = split_dir / "train.parquet"
    val_path = split_dir / "val.parquet"

    if not train_path.exists() or not val_path.exists():
        raise FileNotFoundError(
            "Train/val splits not found. Run split.py before training."
        )

    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)
    train_df[date_col] = pd.to_datetime(train_df[date_col])
    val_df[date_col] = pd.to_datetime(val_df[date_col])

    model_path = train_model(
        train_df=train_df,
        val_df=val_df,
        cfg=cfg,
        model_dir=normal_model_dir,
    )

    print(f"Trained model saved to: {model_path}")


if __name__ == "__main__":
    main()


