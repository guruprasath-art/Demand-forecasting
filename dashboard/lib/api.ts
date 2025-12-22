import axios from "axios";

export const apiClient = axios.create({
  baseURL: "/api",
  timeout: 10000
});

export type ForecastPoint = {
  date: string;
  actual: number | null;
  forecast: number | null;
};

export type ForecastResponse = {
  sku: string;
  horizon: number;
  data: ForecastPoint[];
};

export type MetricsResponse = {
  MAE: number;
  RMSE: number;
  n_samples: number;
};

export type SKUsResponse = {
  skus: string[];
};

export async function fetchSKUs(): Promise<string[]> {
  const res = await apiClient.get<SKUsResponse>("/skus");
  return res.data.skus;
}

export async function fetchForecast(
  sku: string,
  horizon: number
): Promise<ForecastResponse> {
  const res = await apiClient.get<ForecastResponse>(
    `/forecast/${encodeURIComponent(sku)}`,
    {
      params: { horizon }
    }
  );
  return res.data;
}

export async function fetchMetrics(): Promise<MetricsResponse> {
  const res = await apiClient.get<MetricsResponse>("/metrics");
  return res.data;
}

export async function fetchSummary(sku: string, horizon: number): Promise<string> {
  const res = await apiClient.get<{ summary: string }>(`/llm/summary/${encodeURIComponent(sku)}`, {
    params: { horizon }
  });
  return res.data.summary;
}

export async function getModelStatus(): Promise<{ using_fallback: boolean }> {
  const res = await apiClient.get<{ using_fallback: boolean }>(`/model/status`);
  return res.data;
}

export async function startTraining(): Promise<{ status: string }> {
  // Backend may not implement a training POST endpoint; handle errors on caller
  const res = await apiClient.post(`/train`);
  return res.data;
}

export type OverviewSeriesPoint = { date: string; actual?: number; forecast?: number };

export type OverviewResponse = {
  total_forecast_units: number;
  total_forecast_value: number;
  forecast_accuracy: any;
  inventory_risk_score: number;
  stockout_probability: number;
  overstock_risk: number;
  revenue_at_risk: number;
  actual_series: { date: string; actual: number }[];
  predicted_series: { date: string; forecast: number }[];
};

export async function fetchOverview(horizon = 14): Promise<OverviewResponse> {
  const res = await apiClient.get<OverviewResponse>(`/overview`, { params: { horizon } });
  return res.data;
}
