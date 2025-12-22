"use client";

import { useState } from "react";
import type { ForecastPoint } from "../lib/api";

function toCSV(data: ForecastPoint[]) {
  const headers = ["date", "actual", "forecast"];
  const rows = data.map((d) => `${d.date},${d.actual ?? ""},${d.forecast ?? ""}`);
  return [headers.join(","), ...rows].join("\n");
}

export function ForecastDetails({ data }: { data: ForecastPoint[] }) {
  const [copied, setCopied] = useState(false);

  function downloadCSV() {
    const csv = toCSV(data);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "forecast.csv";
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="card">
      <div className="card-title">Forecast Details</div>
      <div className="flex flex-col gap-2">
        <div className="overflow-auto max-h-48">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-slate-400">
                <th className="text-left">Date</th>
                <th className="text-right">Actual</th>
                <th className="text-right">Forecast</th>
              </tr>
            </thead>
            <tbody>
              {data.map((d) => (
                <tr key={d.date} className="border-t border-slate-800">
                  <td className="py-1">{d.date}</td>
                  <td className="py-1 text-right">{d.actual ?? "—"}</td>
                  <td className="py-1 text-right">{d.forecast?.toFixed(2) ?? "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="flex gap-2">
          <button className="btn" onClick={downloadCSV} disabled={data.length === 0}>
            Download CSV
          </button>
          <button
            className="btn-ghost"
            onClick={() => {
              navigator.clipboard?.writeText(JSON.stringify(data))?.then(() => setCopied(true));
            }}
            disabled={data.length === 0}
          >
            Copy JSON
          </button>
          {copied ? <span className="text-xs text-slate-400">Copied</span> : null}
        </div>
      </div>
    </div>
  );
}
