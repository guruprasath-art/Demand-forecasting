import "./globals.css";
import type { ReactNode } from "react";
import { Navbar } from "../components/Navbar";

export const metadata = {
  title: "Demand Forecasting Dashboard",
  description: "Production-grade demand forecasting analytics UI"
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-950 text-slate-50">
        <div className="flex min-h-screen flex-col">
          <Navbar />
          <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 px-4 pb-8 pt-6">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}


