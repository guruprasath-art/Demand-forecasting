from __future__ import annotations

from typing import Iterable, List

class SimpleModel:
    """A tiny predictor used as a fallback when sklearn is unavailable.

    This model is a placeholder; forecasting logic should prefer using the
    iterative recent-targets exponential smoothing implemented in
    `forecasting._iterative_forecast_for_sku` when `_fallback` is True.
    """

    def predict(self, X: Iterable[Iterable[float]]) -> List[float]:
        # Simple constant fallback: return 1.0 for each row to indicate low
        # but non-zero demand. The real iterative logic will compute better
        # forecasts using historical recent_targets when fallback is enabled.
        return [1.0 for _ in X]


class SimpleEncoder:
    def __init__(self, df=None):
        self._map = {}
        if df is not None and "sku" in df.columns:
            uniq = list(df["sku"].astype(str).unique())
            self._map = {s: i for i, s in enumerate(uniq)}

    def transform(self, items: Iterable[str]) -> List[int]:
        return [self._map.get(str(i), 0) for i in items]
