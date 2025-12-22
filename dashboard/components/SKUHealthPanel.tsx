"use client";

import { useEffect, useState } from "react";
import { apiClient } from "../lib/api";

type SKUHealth = {
  sku: string;
  avg: number;
  std: number;
  volatility: number;
  status: "low" | "sufficient";
};

export function SKUHealthPanel({ onSelect }: { onSelect?: (sku: string) => void }) {
  const [items, setItems] = useState<SKUHealth[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        console.log("SKUHealthPanel: fetching /api/sku_health");
        const res = await apiClient.get<{ skus: SKUHealth[] }>("/sku_health");
        setItems(res.data.skus || []);
        console.log("SKUHealthPanel: loaded", (res.data.skus || []).length);
      } catch (e: any) {
        console.error("SKUHealthPanel: error", e);
        setError(e?.response?.data?.detail ?? String(e));
      } finally {
        setLoading(false);
      }
    }

    load();
  }, []);

  const lowAll = items.filter((i) => i.status === "low");
  const sufficientAll = items.filter((i) => i.status === "sufficient");
  const start = (page - 1) * pageSize;
  const low = lowAll.slice(start, start + pageSize);
  const sufficient = sufficientAll.slice(start, start + pageSize);
  const totalPages = Math.max(1, Math.ceil(items.length / (pageSize || 1)));

  return (
    <div className="card">
      <div className="card-title">SKU Health</div>
      <div className="text-sm text-slate-400">Shows recent demand health for SKUs (sample).</div>
      <div className="mt-2 grid grid-cols-2 gap-4">
        <div>
          <div className="text-xs text-slate-300">Low demand (sample)</div>
              <div className="flex items-center justify-between">
                <div className="text-xs text-slate-300">Low demand</div>
                <div className="text-xs text-slate-400">Page {page} / {totalPages}</div>
              </div>
              {loading ? (
            <div className="text-sm text-slate-500">Loading…</div>
          ) : error ? (
            <div className="text-sm text-rose-400">{error}</div>
          ) : (
            <ul className="text-sm text-slate-200 space-y-1">
                  {low.map((s) => (
                    <li key={s.sku} className="hover:bg-slate-800/30 p-1 rounded cursor-pointer" onClick={() => { console.log('SKUHealthPanel: clicked', s.sku); onSelect?.(s.sku); }}>
                      <strong>{s.sku}</strong> — avg: {s.avg.toFixed(2)}, vol: {s.volatility.toFixed(2)}
                    </li>
                  ))}
            </ul>
          )}
              <div className="mt-2 flex items-center gap-2">
                <button className="btn btn-sm" onClick={() => setPage(Math.max(1, page - 1))} disabled={page === 1}>Prev</button>
                <button className="btn btn-sm" onClick={() => setPage(Math.min(totalPages, page + 1))} disabled={page === totalPages}>Next</button>
                <select value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }} className="bg-slate-800 text-slate-100 p-1 rounded text-xs">
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
                <div className="text-xs text-slate-400">Showing {start + 1}-{Math.min(start + pageSize, lowAll.length)} of {lowAll.length} low</div>
              </div>
        </div>
        <div>
          <div className="text-xs text-slate-300">Sufficient demand</div>
          {loading ? (
            <div className="text-sm text-slate-500">Loading…</div>
          ) : error ? (
            <div className="text-sm text-rose-400">{error}</div>
          ) : (
            <ul className="text-sm text-slate-200 space-y-1">
              {sufficient.map((s) => (
                <li key={s.sku} className="hover:bg-slate-800/30 p-1 rounded cursor-pointer" onClick={() => { console.log('SKUHealthPanel: clicked', s.sku); onSelect?.(s.sku); }}>
                  <strong>{s.sku}</strong> — avg: {s.avg.toFixed(2)}, vol: {s.volatility.toFixed(2)}
                </li>
              ))}
            </ul>
          )}
          <div className="mt-2 text-xs text-slate-400">Showing {Math.min(start + 1, sufficientAll.length)}-{Math.min(start + pageSize, sufficientAll.length)} of {sufficientAll.length} sufficient</div>
        </div>
      </div>
    </div>
  );
}
