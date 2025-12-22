from typing import List, Optional

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ForecastPoint(BaseModel):
    date: str
    actual: Optional[float] = None
    forecast: Optional[float] = None


class ForecastResponse(BaseModel):
    sku: str
    horizon: int
    data: List[ForecastPoint]


class MetricsResponse(BaseModel):
    MAE: float
    RMSE: float
    n_samples: int


class SKUsResponse(BaseModel):
    skus: List[str]


class ExecutivePulsePoint(BaseModel):
    date: str
    actual: Optional[float]
    forecast: Optional[float]


class ExecutivePulseResponse(BaseModel):
    total_forecast_units: float
    total_forecast_value: float
    inventory_health_score: float
    projected_stockout_count: int
    projected_stockout_value: float
    excess_capital_value: float
    actual_series: List[ExecutivePulsePoint]
    predicted_series: List[ExecutivePulsePoint]


