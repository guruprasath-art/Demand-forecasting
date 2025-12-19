from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.services.forecasting import forecast_sku, list_skus
from .data_loader import load_config
from .schemas import (
    ForecastPoint,
    ForecastResponse,
    HealthResponse,
    MetricsResponse,
    SKUsResponse,
)

app = FastAPI(title="Demand Forecasting API", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/skus", response_model=SKUsResponse)
def get_skus() -> SKUsResponse:
    skus = list_skus()
    return SKUsResponse(skus=skus)


@app.get("/metrics", response_model=MetricsResponse)
def get_metrics() -> MetricsResponse:
    cfg = load_config()
    metrics_dir = Path(cfg["paths"]["metrics_dir"])
    metrics_path = metrics_dir / "metrics.json"
    if not metrics_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Metrics not found. Run evaluation step to generate metrics.",
        )

    import json

    with metrics_path.open("r") as f:
        data = json.load(f)

    return MetricsResponse(**data)


@app.get("/forecast/{sku}", response_model=ForecastResponse)
def get_forecast(sku: str, horizon: int = 14) -> ForecastResponse:
    """
    Return forecast for a given SKU and horizon.
    The response shape is compatible with the existing Next.js dashboard:
      {
        "sku": "...",
        "horizon": 14,
        "data": [{ "date": "YYYY-MM-DD", "actual": null, "forecast": 123 }]
      }
    """
    allowed_horizons: List[int] = [7, 14, 30]
    if horizon not in allowed_horizons:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid horizon {horizon}. Allowed: {allowed_horizons}",
        )

    skus = list_skus()
    if sku not in skus:
        raise HTTPException(status_code=404, detail=f"Unknown SKU '{sku}'.")

    forecast_df = forecast_sku(sku=sku, horizon=horizon)

    points: List[ForecastPoint] = []
    for _, row in forecast_df.iterrows():
        points.append(
            ForecastPoint(
                date=row["date"].date().isoformat(),
                actual=None,
                forecast=float(row["forecast"]),
            )
        )

    return ForecastResponse(sku=sku, horizon=horizon, data=points)

