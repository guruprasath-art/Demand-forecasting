from pathlib import Path
import os
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.services.forecasting import forecast_sku, list_skus
from app.services.llm import summarize_forecast
from pathlib import Path
from .data_loader import load_config
from .schemas import (
    ForecastPoint,
    ForecastResponse,
    HealthResponse,
    MetricsResponse,
    SKUsResponse,
    ExecutivePulseResponse,
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
    # Prefer a live BigQuery-backed SKU list when available to avoid
    # returning potentially stale values coming from the fallback artifact.
    try:
        from app.data.bigquery_client import list_skus as bq_list_skus

        skus = bq_list_skus()
    except Exception:
        try:
            # Fall back to the artifact-backed SKU list if BigQuery isn't reachable
            skus = list_skus()
        except Exception:
            skus = []

    # Deduplicate SKUs while preserving order to avoid duplicate option keys
    try:
        seen = set()
        unique = []
        for s in skus:
            if s not in seen:
                seen.add(s)
                unique.append(s)
    except Exception:
        unique = skus

    return SKUsResponse(skus=unique)


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

    # Indicate whether the server is using the fallback artifact via header
    return ForecastResponse(sku=sku, horizon=horizon, data=points)


@app.get("/model/status")
def model_status():
    """Return whether a trained artifact is present and whether fallback is active."""
    try:
        from app.services.forecasting import MODEL_PATH
        import importlib

        using_fallback = False
        if not Path(MODEL_PATH).exists():
            using_fallback = True
        else:
            # If sklearn can't be imported, we likely can't unpickle the real model
            try:
                importlib.import_module("sklearn")
            except Exception:
                using_fallback = True

        return {"using_fallback": using_fallback}
    except Exception:
        return {"using_fallback": True}


@app.get("/llm/summary/{sku}")
def get_llm_summary(sku: str, horizon: int = 14):
    """Return an LLM-generated summary for a SKU forecast."""
    allowed_horizons: List[int] = [7, 14, 30]
    if horizon not in allowed_horizons:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid horizon {horizon}. Allowed: {allowed_horizons}",
        )

    try:
        # Do not call list_skus() (this may load model artifact). Attempt to forecast directly.
        forecast_df = forecast_sku(sku=sku, horizon=horizon)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ModuleNotFoundError as e:
        # Likely missing runtime dependency for loading artifact (e.g., scikit-learn)
        raise HTTPException(
            status_code=503,
            detail=(
                "Model runtime dependency missing: "
                f"{e}. Install required packages and restart the server."
            ),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Forecast generation failed: {e}")

    points = []
    try:
        for _, row in forecast_df.iterrows():
            points.append({"date": row["date"].date().isoformat(), "forecast": float(row["forecast"])})
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Invalid forecast data: {e}")

    try:
        summary = summarize_forecast(sku, points)
    except Exception as e:
        # summarize_forecast should handle its own errors, but guard here too
        raise HTTPException(status_code=502, detail=f"LLM summary failed: {e}")

    return {"summary": summary}


@app.get("/internal/llm/probe")
def internal_llm_probe():
    """Internal diagnostic endpoint to probe the configured OpenAI model.
    Returns a sanitized provider response and must not expose the API key.
    """
    try:
        from app.services.llm import probe_model

        return probe_model()
    except Exception as e:
        raise HTTPException(status_code=500, detail="LLM probe failed")


@app.get("/overview")
def get_overview(horizon: int = 14):
    """Return executive overview KPIs and aggregate time series."""
    try:
        from app.services.overview import compute_overview

        return compute_overview(horizon=horizon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Overview generation failed: {e}")


@app.get("/executive/pulse", response_model=ExecutivePulseResponse)
def get_executive_pulse(horizon: int = 14):
    """Return high-level executive KPIs for the dashboard Pulse panel."""
    try:
        from app.services.executive import compute_pulse

        return compute_pulse(horizon=horizon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Executive pulse generation failed: {e}")


@app.get("/sku_health")
def get_sku_health(horizon: int = 14):
    """Return per-SKU health metrics for the dashboard to consume."""
    try:
        from app.services.overview import compute_sku_health

        return compute_sku_health(horizon=horizon)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"SKU health generation failed: {e}")


@app.post("/train")
def trigger_training():
    """Trigger a short training run in the background and return immediately.
    This spawns the repository's training script using the same Python
    interpreter running the API so virtualenvs and PATH remain consistent.
    """
    try:
        import subprocess
        import sys
        from pathlib import Path

        repo_dir = Path(__file__).resolve().parent
        script = repo_dir / "training" / "run_train_short.py"
        # Use repository root (parent of `app`) as working directory so
        # `app` is importable when the training script spawns as a subprocess.
        repo_root = repo_dir.parent
        if not script.exists():
            raise HTTPException(status_code=404, detail="Training script not found")

        # Spawn detached background process so the request returns quickly.
        env = dict(**os.environ)
        # Ensure the training subprocess can import the `app` package by
        # setting PYTHONPATH to the repository root.
        env["PYTHONPATH"] = str(repo_root)
        subprocess.Popen([sys.executable, str(script)], cwd=str(repo_root), env=env)
        return {"status": "started"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

