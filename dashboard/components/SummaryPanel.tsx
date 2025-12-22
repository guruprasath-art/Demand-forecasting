"use client";

import { useState } from "react";
import { fetchSummary } from "../lib/api";

export function SummaryPanel({ sku, horizon }: { sku: string | null; horizon: number }) {
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate() {
    if (!sku) return;
    setLoading(true);
    setError(null);
    setSummary(null);
    try {
      const s = await fetchSummary(sku, horizon);
      setSummary(s);
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? String(e));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="card-title">LLM Summary</div>
      <div className="flex flex-col gap-3">
        <div className="text-sm text-slate-400">Generate an explainable summary for the selected SKU.</div>
        <div className="flex items-center gap-2">
          <button className="btn" disabled={!sku || loading} onClick={handleGenerate}>
            {loading ? "Generating…" : "Generate Summary"}
          </button>
          <span className="text-xs text-slate-400">Horizon: {horizon}d</span>
        </div>
        {error ? <div className="text-sm text-rose-400">{error}</div> : null}
        {summary ? <div className="prose max-w-none text-sm text-slate-100">{summary}</div> : null}
      </div>
    </div>
  );
}
