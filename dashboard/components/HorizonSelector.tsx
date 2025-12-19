"use client";

const OPTIONS = [7, 14, 30] as const;

type HorizonSelectorProps = {
  value: number;
  onChange: (h: number) => void;
};

export function HorizonSelector({ value, onChange }: HorizonSelectorProps) {
  return (
    <div className="card flex flex-col gap-2">
      <div className="card-title">Forecast Horizon</div>
      <div className="flex gap-2">
        {OPTIONS.map((opt) => (
          <button
            key={opt}
            type="button"
            onClick={() => onChange(opt)}
            className={`h-9 flex-1 rounded-md border text-sm transition ${
              value === opt
                ? "border-sky-500 bg-sky-500/10 text-sky-200"
                : "border-slate-700 bg-slate-900 text-slate-200 hover:border-sky-500/60"
            }`}
          >
            {opt} days
          </button>
        ))}
      </div>
    </div>
  );
}


