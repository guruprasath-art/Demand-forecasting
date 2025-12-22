"use client";

import { useEffect, useState } from "react";
import { getModelStatus } from "../lib/api";

export function ModelStatus() {
  const [usingFallback, setUsingFallback] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    getModelStatus()
      .then((r) => mounted && setUsingFallback(r.using_fallback))
      .catch(() => mounted && setUsingFallback(true))
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
  }, []);

  return (
    <div className="card">
      <div className="card-title">Model Status</div>
      <div className="text-sm">
        {loading ? (
          <span className="text-slate-400">Checking model status…</span>
        ) : usingFallback ? (
          <span className="text-amber-300">Using fallback model — consider retraining.</span>
        ) : (
          <span className="text-emerald-400">Trained model available.</span>
        )}
      </div>
    </div>
  );
}
