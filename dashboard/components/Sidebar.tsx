"use client";

import Link from "next/link";

const items = [
  "Overview",
  "Store Performance",
  "Product Demand",
  "Forecasting",
  "Inventory Optimization",
  "Scenario Simulation",
  "Anomalies & Alerts",
  "AI Insights",
  "Reports",
  "Data Health & Model Monitoring",
  "Settings & Access Control",
];

export function Sidebar({ onSelect }: { onSelect?: (item: string) => void }) {
  return (
    <aside className="w-64 bg-slate-900 text-slate-200 min-h-screen p-4">
      <div className="mb-6 flex items-center gap-3">
        <div className="h-10 w-10 rounded bg-emerald-400" />
        <div>
          <div className="font-semibold">DemandOps</div>
          <div className="text-xs text-slate-300">Forecasting Suite</div>
        </div>
      </div>

      <nav className="space-y-1 text-sm">
        {items.map((it) => (
          <a
            key={it}
            href="#"
            onClick={(e) => {
              e.preventDefault();
              onSelect?.(it);
            }}
            className="flex items-center gap-3 p-2 rounded hover:bg-slate-800"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" className="text-slate-300">
              <rect x="3" y="3" width="7" height="7" stroke="currentColor" strokeWidth="1.2" />
              <rect x="14" y="3" width="7" height="7" stroke="currentColor" strokeWidth="1.2" />
            </svg>
            <span>{it}</span>
          </a>
        ))}
      </nav>
    </aside>
  );
}
