"use client";

import { useState } from "react";
import { startTraining } from "../lib/api";

export function TrainButton() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  async function handleTrain() {
    setLoading(true);
    setMessage(null);
    console.log("TrainButton: clicked start training");
    try {
      const res = await startTraining();
      console.log("TrainButton: training API response", res);
      setMessage(res?.status ?? "Training started.");
    } catch (e: any) {
      console.error("TrainButton: training error", e);
      setMessage(
        e?.response?.data?.detail ??
          "Training endpoint not available. Run training via the backend scripts."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card">
      <div className="card-title">Training</div>
      <div className="flex flex-col gap-2">
        <button className="btn" onClick={handleTrain} disabled={loading}>
          {loading ? "Starting…" : "Start Training"}
        </button>
        {message ? <div className="text-sm text-slate-200">{message}</div> : null}
      </div>
    </div>
  );
}
