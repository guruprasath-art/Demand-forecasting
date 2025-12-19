"use client";

type SKUSelectorProps = {
  skus: string[];
  value: string | null;
  onChange: (sku: string) => void;
  disabled?: boolean;
};

export function SKUSelector({
  skus,
  value,
  onChange,
  disabled
}: SKUSelectorProps) {
  return (
    <div className="card flex flex-col gap-2">
      <div className="card-title">SKU</div>
      <select
        className="h-10 rounded-md border border-slate-700 bg-slate-900 px-3 text-sm text-slate-50 shadow-sm outline-none ring-sky-500/40 focus:border-sky-500 focus:ring-2"
        value={value ?? ""}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled || skus.length === 0}
      >
        <option value="" disabled>
          {skus.length === 0 ? "No SKUs available" : "Select a SKU"}
        </option>
        {skus.map((sku) => (
          <option key={sku} value={sku}>
            {sku}
          </option>
        ))}
      </select>
    </div>
  );
}


