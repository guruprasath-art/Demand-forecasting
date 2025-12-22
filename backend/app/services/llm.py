from __future__ import annotations

import os
from typing import List, Dict

import requests
import logging
from dotenv import load_dotenv

# Load .env from backend/ for local development
load_dotenv()


def _call_openai(prompt: str, max_tokens: int = 256) -> str:
    """Call OpenAI Chat Completions API with a single user message and
    return the assistant text. Reads `OPENAI_API_KEY` and optional
    `OPENAI_MODEL` from env. Defaults to `gpt-3.5-turbo`.
    """
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        logging.exception("OpenAI API request failed")
        raise

    # Chat response in choices[0].message.content
    try:
        return data.get("choices", [])[0].get("message", {}).get("content", "")
    except Exception:
        return ""


def summarize_forecast(sku: str, points: List[Dict[str, object]]) -> str:
    """
    Produce a human-readable summary for a SKU forecast using OpenAI.

    `points` is a list of dicts with keys: `date` (ISO str) and `forecast` (float).
    """
    if not points:
        return "No forecast data available to summarize."

    # Build a concise prompt with the forecast table and instructions
    lines = [f"SKU: {sku}", "Forecast (date -> value):"]
    for p in points:
        lines.append(f"- {p.get('date')}: {p.get('forecast')}")

    prompt = (
        "\n".join(lines)
        + "\n\nPlease provide a short summary (3-5 sentences) describing the trend, any notable peaks or drops, the average forecast, and one practical recommendation for demand planning."
    )

    try:
        return _call_openai(prompt)
    except Exception:
        logging.exception("summarize_forecast: LLM call failed for SKU %s, using local fallback", sku)
        # Fall back to a deterministic local summarizer so the dashboard
        # continues to provide helpful insight even without remote LLM access.
        return _local_summarize(sku, points)


def _local_summarize(sku: str, points: List[Dict[str, object]]) -> str:
    """Produce a concise, human-readable summary from numeric forecast points.

    The summary includes: overall trend, notable peak/drop, average forecast,
    and a practical recommendation. This is intentionally deterministic and
    dependency-free so it can run in offline or restricted environments.
    """
    try:
        vals = [float(p.get("forecast", 0.0)) for p in points]
        dates = [p.get("date") for p in points]
        if not vals:
            return "No forecast data available to summarize."

        n = len(vals)
        avg = sum(vals) / n
        first, last = vals[0], vals[-1]
        change = (last - first) / (abs(first) + 1e-9)

        # Trend description
        if abs(change) < 0.02:
            trend = "stable with little change"
        elif change > 0:
            trend = f"increasing (≈{change*100:.1f}% over the horizon)"
        else:
            trend = f"decreasing (≈{abs(change)*100:.1f}% over the horizon)"

        # Peak / drop
        max_val = max(vals)
        min_val = min(vals)
        max_idx = vals.index(max_val)
        min_idx = vals.index(min_val)
        peak_phrase = f"peak of {max_val:.2f} on {dates[max_idx]}" if max_val > avg else "no clear peak above average"
        drop_phrase = f"drop to {min_val:.2f} on {dates[min_idx]}" if min_val < avg else "no clear drop below average"

        # Volatility
        import math

        variance = sum((v - avg) ** 2 for v in vals) / max(1, n - 1)
        std = math.sqrt(variance)
        volatility = "low" if std / (avg + 1e-9) < 0.05 else "moderate" if std / (avg + 1e-9) < 0.15 else "high"

        rec = "Monitor inventory and adjust safety stock for observed changes."
        if change > 0.05:
            rec = "Increase reorder quantities slightly to avoid stockouts as demand rises."
        elif change < -0.05:
            rec = "Reduce incoming inventory or re-evaluate promotions as demand falls."

        sentences = [
            f"SKU {sku}: forecast is {trend} with {volatility} volatility.",
            f"Average forecast over the horizon is {avg:.2f}; {peak_phrase}; {drop_phrase}.",
            rec,
        ]
        return " ".join(sentences)
    except Exception:
        logging.exception("_local_summarize failed")
        return "Unable to generate local summary." 


def probe_model() -> Dict[str, object]:
    """Probe the configured model with a tiny test prompt and return a
    sanitized result dict containing the HTTP status and the provider body.
    This helper is intended for diagnostics and will NOT return the API key.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    if not api_key:
        return {"status": "missing_key", "body": "OPENAI_API_KEY not set"}

    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    body = {"model": model, "messages": [{"role": "user", "content": "probe"}], "max_tokens": 8}
    try:
        resp = requests.post(url, headers=headers, json=body, timeout=10)
        status = resp.status_code
        try:
            data = resp.json()
        except Exception:
            data = {"text": resp.text}
        return {"status": status, "body": data}
    except Exception as e:
        logging.exception("probe_model: request failed")
        return {"status": "error", "body": str(e)}
