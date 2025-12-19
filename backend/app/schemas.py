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


