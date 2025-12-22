"use client";

import { useEffect, useState } from "react";
import { fetchOverview, OverviewResponse } from "../lib/api";
import { ForecastChart } from "../components/ForecastChart";
import { Card } from "../components/Card";
import { KPI } from "./KPI";
import {
  LineChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";

export function OverviewPanel({ horizon }: { horizon: number }) {
  const [data, setData] = useState<OverviewResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchOverview(horizon)
      .then((r) => setData(r))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [horizon]);

  if (loading) {
    return (
      <div className="grid grid-cols-3 gap-4">
        <Card title="Total Forecasted Demand">Loading…</Card>
        <Card title="Forecast Accuracy">Loading…</Card>
        <Card title="Inventory Risk">Loading…</Card>
      </div>
    );
  }

  if (!data) {
    return <div className="text-sm text-rose-400">Overview data unavailable</div>;
  }

  const chartData = [] as any[];
  // merge last actuals and predicted
  data.actual_series.forEach((p) => chartData.push({ date: p.date, actual: p.actual, forecast: null }));
  data.predicted_series.forEach((p) => chartData.push({ date: p.date, actual: null, forecast: p.forecast }));

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-4">
        <KPI
          label="Total Forecasted Demand"
          value={data.total_forecast_units.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          subtitle={`Units over next ${horizon} days`}
          spark={
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.predicted_series.map((p) => ({ date: p.date, v: p.forecast }))}>
                <Line type="monotone" dataKey="v" stroke="#38bdf8" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          }
        />

        <KPI
          label="Total Forecast Value"
          value={`$${data.total_forecast_value.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
          subtitle="Estimated value at avg price"
          spark={
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.predicted_series.map((p, i) => ({ date: p.date, v: p.forecast * (1 + (i % 5) * 0.005) }))}>
                <Line type="monotone" dataKey="v" stroke="#60a5fa" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          }
        />

        <KPI
          label="Inventory Risk"
          value={`${(data.inventory_risk_score * 100).toFixed(1)}%`}
          subtitle="Risk score"
          spark={
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={data.predicted_series.map((p, i) => ({ date: p.date, v: Math.max(0, 100 - (p.forecast ?? 0) * 0.1) }))}>
                <Line type="monotone" dataKey="v" stroke="#f97316" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          }
        />
      </div>

      <Card title="Actual vs Predicted (aggregate)">
        <ForecastChart
          data={chartData.map((d) => ({ date: d.date, actual: d.actual ?? null, forecast: d.forecast ?? null }))}
          loading={false}
        />
      </Card>
    </div>
  );
}
