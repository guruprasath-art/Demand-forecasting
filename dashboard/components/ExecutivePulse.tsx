"use client";

import { useEffect, useState } from "react";
import { apiClient } from "../lib/api";
import { Card } from "./Card";
import { KPI } from "./KPI";

type Point = { date: string; actual?: number; forecast?: number };

export function ExecutivePulse({ horizon = 14 }: { horizon?: number }) {
  const [data, setData] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const res = await apiClient.get(`/executive/pulse?horizon=${horizon}`);
        setData(res.data);
      } catch (e: any) {
        console.error("ExecutivePulse: error", e);
        setError(e?.response?.data?.detail ?? String(e));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [horizon]);

  if (loading) return <div className="card">Loading Executive Pulse…</div>;
  if (error) return <div className="card text-rose-400">{error}</div>;
  if (!data) return null;

  return (
    <div className="card">
      <div className="card-title">Executive Pulse</div>
      <div className="grid grid-cols-2 gap-4">
        <KPI label="Total Forecast Units" value={String(Math.round(data.total_forecast_units))} subtitle={`Horizon: ${horizon}d`} />
        <KPI label="Inventory Health" value={`${data.inventory_health_score.toFixed(1)}%`} subtitle="Percent SKUs sufficient" />
        <KPI label="Projected Stockouts" value={`${data.projected_stockout_count}`} subtitle={`Value: ${Math.round(data.projected_stockout_value)}`} />
        <KPI label="Excess Capital" value={`${Math.round(data.excess_capital_value)}`} subtitle="Estimated revenue at risk" />
      </div>
    </div>
  );
}
