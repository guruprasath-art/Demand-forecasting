import axios from "axios";

export const apiClient = axios.create({
  baseURL: "http://localhost:8000",
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


