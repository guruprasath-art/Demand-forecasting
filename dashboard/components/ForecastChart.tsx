"use client";

import {
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
  CartesianGrid
} from "recharts";
import type { ForecastPoint } from "../lib/api";

type ForecastChartProps = {
  data: ForecastPoint[];
  loading: boolean;
};

export function ForecastChart({ data, loading }: ForecastChartProps) {
  return (
    <div className="card h-[360px]">
      <div className="mb-3 flex items-center justify-between">
        <div className="card-title">Demand Forecast</div>
        {loading && (
          <span className="text-xs text-slate-400">Loading forecast…</span>
        )}
      </div>
      <div className="h-[300px]">
        {data.length === 0 ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-500">
            No data to display. Select a SKU to view its demand profile.
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#cbd5f5" }}
                tickMargin={10}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#cbd5f5" }}
                tickMargin={8}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#020617",
                  border: "1px solid #1e293b",
                  borderRadius: "0.5rem",
                  fontSize: "0.75rem"
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="actual"
                name="Actual"
                stroke="#22c55e"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="forecast"
                name="Forecast"
                stroke="#38bdf8"
                strokeWidth={2}
                dot={false}
                strokeDasharray="5 4"
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}


