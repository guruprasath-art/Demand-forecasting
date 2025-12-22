"use client";
import type { ReactNode } from "react";

type KPIProps = {
  label: string;
  value: string | number;
  subtitle?: string;
  spark?: ReactNode;
};

export function KPI({ label, value, subtitle, spark }: KPIProps) {
  return (
    <div className="card p-4 flex flex-col justify-between">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-medium text-slate-300">{label}</div>
          <div className="text-2xl font-semibold text-white mt-1">{value}</div>
        </div>
        {spark ? <div className="w-28 h-10">{spark}</div> : null}
      </div>
      {subtitle && (
        <div className="mt-2 text-xs text-slate-400">{subtitle}</div>
      )}
    </div>
  );
}


