"use client";

export function Navbar() {
  return (
    <header className="border-b border-slate-800 bg-slate-950/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-md bg-sky-500/80" />
          <div className="flex flex-col">
            <span className="text-sm font-semibold tracking-wide text-slate-50">
              Demand Forecasting
            </span>
            <span className="text-xs text-slate-400">
              Retail &amp; Ecommerce Demand Intelligence
            </span>
          </div>
        </div>
      </div>
    </header>
  );
}


