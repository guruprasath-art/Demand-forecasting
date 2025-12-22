"use client";

import { useEffect, useState } from "react";
import { fetchOverview } from "../lib/api";
import { Card } from "./Card";

export function StorePerformance({ horizon = 14 }: { horizon?: number }) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await fetchOverview(horizon);
        setData(res);
      } catch (e: any) {
        console.error("StorePerformance: error", e);
        setError(e?.response?.data?.detail ?? String(e));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [horizon]);

  return (
    <Card title="Store Performance">
      {loading ? (
        <div className="text-sm text-slate-400">Loading…</div>
      ) : error ? (
        <div className="text-sm text-rose-400">{error}</div>
      ) : data ? (
        <div className="text-sm text-slate-200 space-y-2">
          <div>Total forecast units: {Math.round(data.total_forecast_units)}</div>
          <div>Inventory risk score: {Math.round((data.inventory_risk_score || 0) * 100) / 100}</div>
          <div>Predicted series points: {data.predicted_series?.length ?? 0}</div>
          <div className="text-xs text-slate-400">Note: per-store breakdown not available — requires `store_id` dimension in demand history.</div>
        </div>
      ) : (
        <div className="text-sm text-slate-400">No data</div>
      )}
    </Card>
  );
}
