"use client";

import { useEffect, useState } from "react";
import {
  fetchForecast,
  fetchMetrics,
  fetchSKUs,
  type ForecastPoint,
  type MetricsResponse
} from "../lib/api";
import { KPI } from "../components/KPI";
import { SKUSelector } from "../components/SKUSelector";
import { HorizonSelector } from "../components/HorizonSelector";
import { ForecastChart } from "../components/ForecastChart";

export default function Page() {
  const [skus, setSkus] = useState<string[]>([]);
  const [selectedSKU, setSelectedSKU] = useState<string | null>(null);
  const [horizon, setHorizon] = useState<number>(14);
  const [forecastData, setForecastData] = useState<ForecastPoint[]>([]);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loadingForecast, setLoadingForecast] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function bootstrap() {
      try {
        setLoadingInitial(true);
        const [skuList, metricData] = await Promise.all([
          fetchSKUs(),
          fetchMetrics().catch(() => null)
        ]);
        setSkus(skuList);
        if (skuList.length > 0) {
          setSelectedSKU(skuList[0]);
        }
        if (metricData) {
          setMetrics(metricData);
        }
      } catch (err) {
        console.error(err);
        setError(
          "Unable to load initial data. Ensure the FastAPI backend is running on port 8000."
        );
      } finally {
        setLoadingInitial(false);
      }
    }

    bootstrap();
  }, []);

  useEffect(() => {
    async function loadForecast() {
      if (!selectedSKU) {
        setForecastData([]);
        return;
      }
      try {
        setLoadingForecast(true);
        setError(null);
        const response = await fetchForecast(selectedSKU, horizon);
        setForecastData(response.data);
      } catch (err) {
        console.error(err);
        setError(
          "Failed to load forecast. Confirm the backend is running and has a trained model."
        );
      } finally {
        setLoadingForecast(false);
      }
    }

    loadForecast();
  }, [selectedSKU, horizon]);

  const effectiveError = error;

  return (
    <div className="flex flex-col gap-6">
      <section className="grid gap-4 md:grid-cols-3">
        <SKUSelector
          skus={skus}
          value={selectedSKU}
          onChange={setSelectedSKU}
          disabled={loadingInitial}
        />
        <HorizonSelector value={horizon} onChange={setHorizon} />
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <KPI
            label="Selected SKU"
            value={selectedSKU ?? "None"}
            subtitle="SKU currently in focus"
          />
          <KPI
            label="Forecast Horizon"
            value={`${horizon} days`}
            subtitle="Future days predicted"
          />
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-[2fr,1fr]">
        <ForecastChart data={forecastData} loading={loadingForecast} />
        <div className="flex flex-col gap-4">
          <div className="card">
            <div className="card-title mb-2">Model Quality</div>
            {metrics ? (
              <div className="space-y-2 text-sm">
                <div className="flex items-baseline justify-between">
                  <span className="text-slate-400">MAE</span>
                  <span className="text-lg font-semibold text-slate-50">
                    {metrics.MAE.toFixed(2)}
                  </span>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-slate-400">RMSE</span>
                  <span className="text-sm text-slate-100">
                    {metrics.RMSE.toFixed(2)}
                  </span>
                </div>
                <div className="flex items-baseline justify-between">
                  <span className="text-slate-400">Test Samples</span>
                  <span className="text-sm text-slate-100">
                    {metrics.n_samples.toLocaleString()}
                  </span>
                </div>
              </div>
            ) : (
              <p className="text-sm text-slate-500">
                No metrics found yet. Run the evaluation step in the backend to
                compute MAE and RMSE.
              </p>
            )}
          </div>
          <div className="card">
            <div className="card-title mb-2">Status</div>
            {loadingInitial ? (
              <p className="text-sm text-slate-400">
                Initialising dashboard and loading SKUs…
              </p>
            ) : effectiveError ? (
              <p className="text-sm text-rose-400">{effectiveError}</p>
            ) : (
              <p className="text-sm text-emerald-400">
                Connected to backend. Select a SKU to explore demand patterns.
              </p>
            )}
          </div>
        </div>
      </section>
    </div>
  );
}


