from typing import Dict, Any

from .forecasting import load_artifact
from .overview import compute_overview, compute_sku_health


def compute_pulse(horizon: int = 14, low_threshold: float = 1.0) -> Dict[str, Any]:
    """Compute executive KPIs using existing overview and SKU health logic.

    Returns a dict suitable for the dashboard Executive panel. This is
    intentionally lightweight and uses available artifact/history data;
    when inventory snapshots or price history are available they should
    be incorporated to improve the metrics.
    """
    artifact = load_artifact()
    # Use compute_overview for aggregated numbers
    overview = compute_overview(horizon=horizon)

    # Use SKU health to compute inventory health score (fraction sufficient)
    sku_health = compute_sku_health(horizon=horizon, low_threshold=low_threshold)
    skus = sku_health.get("skus", [])
    total_skus = len(skus)
    sufficient = sum(1 for s in skus if s.get("status") == "sufficient")
    inventory_health_score = float((sufficient / total_skus) * 100.0) if total_skus > 0 else 100.0

    # Projected stockout: count of SKUs marked low (approximate) and estimate value
    projected_stockout_count = int(sum(1 for s in skus if s.get("status") == "low"))

    # Estimate projected_stockout_value using overview total_forecast_value distribution
    try:
        total_value = float(overview.get("total_forecast_value", 0.0))
        projected_stockout_value = float(total_value) * (projected_stockout_count / max(1, total_skus))
    except Exception:
        projected_stockout_value = 0.0

    # Excess capital: reuse revenue_at_risk as a conservative proxy
    excess_capital_value = float(overview.get("revenue_at_risk", 0.0))

    return {
        "total_forecast_units": float(overview.get("total_forecast_units", 0.0)),
        "total_forecast_value": float(overview.get("total_forecast_value", 0.0)),
        "inventory_health_score": inventory_health_score,
        "projected_stockout_count": projected_stockout_count,
        "projected_stockout_value": projected_stockout_value,
        "excess_capital_value": excess_capital_value,
        "actual_series": overview.get("actual_series", []),
        "predicted_series": overview.get("predicted_series", []),
    }
