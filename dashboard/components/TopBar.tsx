"use client";

import { useState, useEffect } from "react";
import { fetchSKUs } from "../lib/api";

export function TopBar({ children }: { children?: React.ReactNode }) {
  const [stores, setStores] = useState<string[]>([]);
  const [selectedStore, setSelectedStore] = useState<string | null>(null);

  useEffect(() => {
    fetchSKUs().then((s) => setStores(s)).catch(() => setStores([]));
  }, []);

  return (
    <header className="flex items-center justify-between gap-4 p-4 bg-white/5 border-b border-slate-800">
      <div className="flex items-center gap-3">
        <select value={selectedStore ?? ""} onChange={(e) => setSelectedStore(e.target.value)} className="bg-slate-800 text-slate-100 p-2 rounded">
          <option value="">All SKUs</option>
          {stores.slice(0, 50).map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
        <div className="text-sm text-slate-400">|</div>
        <div className="text-sm text-slate-300">Time Range</div>
      </div>

      <div className="flex items-center gap-3">
        <button className="btn">Export</button>
        <div className="flex items-center gap-2">
          <div className="h-8 w-8 rounded-full bg-slate-600" />
          <div className="text-sm">Guru — Admin</div>
        </div>
      </div>
    </header>
  );
}
