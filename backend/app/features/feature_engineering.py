from __future__ import annotations

from typing import Iterable

import pandas as pd


def build_time_series_features(
    df: pd.DataFrame,
    lags: Iterable[int] = (7, 14, 28),
    rolling_windows: Iterable[int] = (7, 14),
) -> pd.DataFrame:
    """
    Given a DataFrame with columns ['date', 'sku', 'total_quantity'],
    generate lag, rolling mean, and calendar features per-SKU.
    """
    required_cols = {"date", "sku", "total_quantity"}
    missing = required_cols.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["sku", "date"])

    for lag in lags:
        df[f"lag_{lag}"] = (
            df.groupby("sku")["total_quantity"]
            .shift(lag)
            .astype(float)
        )

    for window in rolling_windows:
        df[f"rolling_mean_{window}"] = (
            df.groupby("sku")["total_quantity"]
            .shift(1)
            .rolling(window=window)
            .mean()
            .astype(float)
        )

    # Calendar features
    df["day_of_week"] = df["date"].dt.dayofweek.astype(int)
    df["month"] = df["date"].dt.month.astype(int)

    return df


