import React, { useEffect, useState } from "react";
import { getKpis } from "../services/api";
import KpiCard from "../components/KpiCard";

export default function Dashboard() {
  const [kpis, setKpis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // fetch all-time KPIs on load
  useEffect(() => {
    setLoading(true);
    getKpis()
      .then((data) => {
        setKpis(data);
        setError(null);
      })
      .catch((err) => {
        console.error("API error:", err);
        setError(err?.message || "Failed to fetch KPIs");
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold">Retail Analytics Dashboard</h1>
        <p className="text-sm text-gray-500">Overview — KPI cards (Total revenue, orders, units, profit)</p>
      </header>

      {loading && <div className="text-gray-600">Loading KPIs…</div>}
      {error && <div className="text-red-600">Error: {error}</div>}

      {kpis && (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <KpiCard title="Total Revenue" value={kpis.total_revenue} subtitle="Selected range" isCurrency={true} />
          <KpiCard title="Total Orders" value={kpis.total_orders} subtitle="Unique orders" />
          <KpiCard title="Units Sold" value={kpis.total_units_sold} subtitle="Total units" />
          <KpiCard
            title="Gross Profit"
            value={kpis.gross_profit}
            subtitle={`Profit margin ${(kpis.profit_margin * 100).toFixed(2)}%`}
            isCurrency={true}
          />
        </div>
      )}
    </div>
  );
}
