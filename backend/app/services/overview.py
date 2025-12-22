from __future__ import annotations

from datetime import timedelta
from typing import Dict, Any

import numpy as np
import pandas as pd

from .forecasting import load_artifact


def compute_overview(horizon: int = 14) -> Dict[str, Any]:
    """Compute executive-level overview KPIs and aggregated time series.

    This uses the loaded history dataframe (from the artifact) and simple
    heuristics to produce totals, risk scores, and short aggregated time
    series for Actual vs Predicted. The predictions here are lightweight
    aggregates (recent average extended) to avoid expensive model calls.
    """
    artifact = load_artifact()
    history_df: pd.DataFrame = artifact["history_df"].copy()

    if history_df.empty:
        return {
            "total_forecast_units": 0,
            "total_forecast_value": 0,
            "forecast_accuracy": None,
            "inventory_risk_score": 0,
            "stockout_probability": 0,
            "overstock_risk": 0,
            "revenue_at_risk": 0,
            "actual_series": [],
            "predicted_series": [],
        }

    history_df["date"] = pd.to_datetime(history_df["date"])

    # Aggregate recent daily totals (last 90 days)
    end = history_df["date"].max()
    start = end - pd.Timedelta(days=90)
    recent = history_df[history_df["date"] >= start]
    daily = recent.groupby("date")["total_quantity"].sum().reset_index()
    daily = daily.sort_values("date")

    # Compute per-SKU recent averages and a lightweight forecast per SKU
    sku_avgs = (
        recent.groupby("sku")["total_quantity"].mean().rename("avg")
    )

    # Total forecast units = sum(avg * horizon)
    total_forecast_units = float(sku_avgs.sum() * horizon)

    # Price information may be present in history
    if "price" in history_df.columns:
        avg_price = float(history_df["price"].dropna().mean()) if not history_df["price"].dropna().empty else 1.0
    else:
        avg_price = 1.0

    total_forecast_value = total_forecast_units * avg_price

    # Simple inventory risk: normalized volatility across SKUs
    sku_std = recent.groupby("sku")["total_quantity"].std().fillna(0)
    sku_mean = sku_avgs.reindex(sku_std.index)
    volatility = (sku_std / (sku_mean + 1e-9)).replace([np.inf, -np.inf], 0).fillna(0)
    inventory_risk_score = float(min(100.0, (volatility.mean() * 100)))

    # Stockout probability heuristic: proportion of SKUs with very low avg demand
    low_sku_frac = float((sku_avgs < 1.0).sum() / max(1, len(sku_avgs)))
    stockout_probability = float(min(1.0, low_sku_frac * 1.5))

    # Overstock risk heuristic: proportion of SKUs with avg < recent max/3 (proxy)
    overstock_risk = float(min(1.0, (sku_avgs > (sku_avgs.mean() * 2)).sum() / max(1, len(sku_avgs))))

    # Revenue at risk: fraction of forecast value times a volatility factor
    revenue_at_risk = total_forecast_value * (inventory_risk_score / 100.0) * 0.1

    # Build aggregated predicted series: extend recent daily mean forward
    recent_daily_mean = daily["total_quantity"].mean() if not daily.empty else 0.0
    predicted_dates = [end + timedelta(days=i) for i in range(1, horizon + 1)]
    predicted_series = [{"date": d.date().isoformat(), "forecast": float(recent_daily_mean)} for d in predicted_dates]

    actual_series = [
        {"date": row["date"].date().isoformat(), "actual": float(row["total_quantity"])}
        for _, row in daily.iterrows()
    ]

    return {
        "total_forecast_units": total_forecast_units,
        "total_forecast_value": total_forecast_value,
        "forecast_accuracy": None,
        "inventory_risk_score": inventory_risk_score,
        "stockout_probability": stockout_probability,
        "overstock_risk": overstock_risk,
        "revenue_at_risk": revenue_at_risk,
        "actual_series": actual_series,
        "predicted_series": predicted_series,
    }


def compute_sku_health(horizon: int = 14, low_threshold: float = 1.0) -> Dict[str, Any]:
    """Return per-SKU health metrics and simple status flags.

    The response contains a list of SKUs with `sku`, `avg`, `std`,
    `volatility` and a `status` string ("low" | "sufficient").
    """
    artifact = load_artifact()
    history_df: pd.DataFrame = artifact["history_df"].copy()

    if history_df.empty:
        return {"skus": []}

    history_df["date"] = pd.to_datetime(history_df["date"])
    end = history_df["date"].max()
    start = end - pd.Timedelta(days=90)
    recent = history_df[history_df["date"] >= start]

    sku_stats = recent.groupby("sku").agg(
        avg=("total_quantity", "mean"),
        std=("total_quantity", "std"),
    )
    sku_stats["std"] = sku_stats["std"].fillna(0)
    sku_stats["volatility"] = (sku_stats["std"] / (sku_stats["avg"] + 1e-9)).replace([np.inf, -np.inf], 0).fillna(0)

    rows = []
    for sku, row in sku_stats.iterrows():
        avg = float(row["avg"])
        std = float(row["std"])
        vol = float(row["volatility"])
        status = "low" if avg < low_threshold else "sufficient"
        rows.append({"sku": sku, "avg": avg, "std": std, "volatility": vol, "status": status})

    return {"skus": rows}
