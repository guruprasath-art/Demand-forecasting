"use client";

import { useState, useEffect } from "react";

export function TopBar({ children }: { children?: React.ReactNode }) {

  return (
    <header className="flex items-center justify-between gap-4 p-4 bg-white/5 border-b border-slate-800">
      <div className="flex items-center gap-3">
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
