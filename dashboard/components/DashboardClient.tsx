"use client";

import { useEffect, useState } from "react";
import { fetchForecast, fetchMetrics, fetchSKUs } from "../lib/api";
import type { ForecastPoint, MetricsResponse } from "../lib/api";
import { KPI } from "./KPI";
import { SKUSelector } from "./SKUSelector";
import { HorizonSelector } from "./HorizonSelector";
import { ForecastChart } from "./ForecastChart";
import { SummaryPanel } from "./SummaryPanel";
import { ModelStatus } from "./ModelStatus";
import { TrainButton } from "./TrainButton";
import { ForecastDetails } from "./ForecastDetails";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";
import { Card } from "./Card";
import { OverviewPanel } from "./OverviewPanel";

export default function DashboardClient() {
  const [skus, setSkus] = useState<string[]>([]);
  const [selectedSKU, setSelectedSKU] = useState<string | null>(null);
  const [horizon, setHorizon] = useState<number>(14);
  const [forecastData, setForecastData] = useState<ForecastPoint[]>([]);
  const [metrics, setMetrics] = useState<MetricsResponse | null>(null);
  const [loadingForecast, setLoadingForecast] = useState(false);
  const [loadingInitial, setLoadingInitial] = useState(true);
  const [summary, setSummary] = useState<string | null>(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [usingFallback, setUsingFallback] = useState<boolean | null>(null);
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
        // Check model status (fallback or real)
        import("../lib/api").then((m) => m.apiClient.get("/model/status")).then((r) => setUsingFallback(r.data.using_fallback)).catch(() => setUsingFallback(true));
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
    <div className="flex h-screen bg-slate-900 text-slate-100">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <TopBar />
        <main className="p-6 overflow-auto">
          <section className="grid gap-4 md:grid-cols-3">
            <div className="md:col-span-2">
              <OverviewPanel horizon={horizon} />
            </div>
            <div>
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
            </div>
          </section>

          <section className="grid gap-4 md:grid-cols-[2fr,1fr]">
            <div className="space-y-4">
              <ForecastChart data={forecastData} loading={loadingForecast} />
              <ForecastDetails data={forecastData} />
            </div>
            <div className="flex flex-col gap-4">
              <Card title="Model Quality">
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
              </Card>
              <ModelStatus />
              <TrainButton />
              <SummaryPanel sku={selectedSKU} horizon={horizon} />
              <Card title="Status">
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
              </Card>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}
