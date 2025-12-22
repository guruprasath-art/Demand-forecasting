"use client";

export function Card({ title, children }: { title?: string; children?: React.ReactNode }) {
  return (
    <div className="card bg-slate-800 border border-slate-700 p-4 rounded"> 
      {title ? <div className="card-title mb-2 text-sm font-medium">{title}</div> : null}
      <div>{children}</div>
    </div>
  );
}
