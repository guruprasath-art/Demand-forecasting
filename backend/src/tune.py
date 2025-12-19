from pathlib import Path
from typing import Dict, Tuple

import joblib
import numpy as np
import pandas as pd
import yaml
from lightgbm import LGBMRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.model_selection import ParameterSampler
from sklearn.preprocessing import LabelEncoder


def load_config(config_path: Path) -> dict:
    with config_path.open("r") as f:
        return yaml.safe_load(f)


def prepare_xy(
    df: pd.DataFrame,
    cfg: dict,
) -> Tuple[pd.DataFrame, np.ndarray, list[str], LabelEncoder]:
    target_col = cfg["data"]["target_column"]
    date_col = cfg["data"]["date_column"]
    sku_col = cfg["data"]["sku_column"]
    extra_features = cfg["data"].get("extra_feature_columns", [])

    df = df.dropna().copy()

    sku_le = LabelEncoder()
    df[sku_col] = sku_le.fit_transform(df[sku_col].astype(str))

    feature_cols: list[str] = []
    feature_cols.extend(extra_features)
    feature_cols.append(sku_col)

    for col in df.columns:
        if col.startswith(f"{target_col}_lag_") or col.startswith(
            f"{target_col}_rolling_mean_"
        ):
            feature_cols.append(col)

    feature_cols = [c for c in feature_cols if c not in {target_col, date_col}]
    X = df[feature_cols].copy()
    y = df[target_col].values.astype(float)
    return X, y, feature_cols, sku_le


def random_search_tune(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    cfg: dict,
) -> Dict:
    X_train, y_train, feature_cols, sku_le = prepare_xy(train_df, cfg)
    X_val, y_val, _, _ = prepare_xy(val_df, cfg)

    train_cfg = cfg["training"]
    tuning_cfg = cfg["tuning"]

    num_boost_round = train_cfg.get("num_boost_round", 1000)
    early_stopping_rounds = train_cfg.get("early_stopping_rounds", 50)
    random_state = train_cfg.get("random_state", 42)

    param_distributions = tuning_cfg["param_distributions"]
    n_iter = tuning_cfg.get("n_iter", 20)

    sampler = ParameterSampler(
        param_distributions=param_distributions,
        n_iter=n_iter,
        random_state=random_state,
    )

    best_score = float("inf")
    best_params: Dict = {}
    best_model = None

    for params in sampler:
        model = LGBMRegressor(
            n_estimators=num_boost_round,
            random_state=random_state,
            objective="regression",
            **params,
        )
        model.fit(
            X_train,
            y_train,
            eval_set=[(X_val, y_val)],
            eval_metric="l2",
            early_stopping_rounds=early_stopping_rounds,
        )
        preds = model.predict(X_val)
        mae = mean_absolute_error(y_val, preds)
        if mae < best_score:
            best_score = mae
            best_params = params
            best_model = model

    assert best_model is not None

    artifact = {
        "model": best_model,
        "feature_cols": feature_cols,
        "sku_label_encoder": sku_le,
        "config": cfg,
        "best_params": best_params,
        "best_val_mae": best_score,
    }
    return artifact


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Hyperparameter tuning via random search.")
    parser.add_argument(
        "--config",
        type=str,
        default="backend/configs/model.yaml",
        help="Path to YAML config file.",
    )
    args = parser.parse_args()

    cfg = load_config(Path(args.config))
    features_dir = Path(cfg["paths"]["features_data_dir"])
    tuned_model_dir = Path(cfg["paths"]["tuned_model_dir"])
    date_col = cfg["data"]["date_column"]

    split_dir = features_dir / "splits"
    train_path = split_dir / "train.parquet"
    val_path = split_dir / "val.parquet"

    if not train_path.exists() or not val_path.exists():
        raise FileNotFoundError(
            "Train/val splits not found. Run split.py before tuning."
        )

    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)
    train_df[date_col] = pd.to_datetime(train_df[date_col])
    val_df[date_col] = pd.to_datetime(val_df[date_col])

    tuned_model_dir.mkdir(parents=True, exist_ok=True)
    artifact = random_search_tune(train_df=train_df, val_df=val_df, cfg=cfg)
    model_path = tuned_model_dir / "model_tuned.joblib"
    joblib.dump(artifact, model_path)

    print(f"Tuned model saved to: {model_path}")
    print(f"Best params: {artifact['best_params']}")
    print(f"Best validation MAE: {artifact['best_val_mae']:.4f}")


if __name__ == "__main__":
    main()


