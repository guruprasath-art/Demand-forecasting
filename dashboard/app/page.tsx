"use client";

import { useEffect, useState } from "react";
import { fetchForecast, fetchMetrics, fetchSKUs } from "../lib/api";
import type { ForecastPoint, MetricsResponse } from "../lib/api";
import { KPI } from "../components/KPI";
import { SKUSelector } from "../components/SKUSelector";
import { HorizonSelector } from "../components/HorizonSelector";
import { ForecastChart } from "../components/ForecastChart";
import { SummaryPanel } from "../components/SummaryPanel";
import { ModelStatus } from "../components/ModelStatus";
import { TrainButton } from "../components/TrainButton";
import { ForecastDetails } from "../components/ForecastDetails";
import { Sidebar } from "../components/Sidebar";
import { TopBar } from "../components/TopBar";
import { Card } from "../components/Card";
import { OverviewPanel } from "../components/OverviewPanel";

import dynamic from "next/dynamic";

const DashboardClient = dynamic(() => import("../components/DashboardClient"), { ssr: false });

export default function Page() {
  return <DashboardClient />;
}


