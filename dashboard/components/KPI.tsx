"use client";

type KPIProps = {
  label: string;
  value: string;
  subtitle?: string;
};

export function KPI({ label, value, subtitle }: KPIProps) {
  return (
    <div className="card">
      <div className="card-title">{label}</div>
      <div className="card-value">{value}</div>
      {subtitle && (
        <div className="mt-1 text-xs text-slate-400">{subtitle}</div>
      )}
    </div>
  );
}


