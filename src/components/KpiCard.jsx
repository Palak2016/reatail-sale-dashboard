import React from "react";

function formatNumber(v, isCurrency = false) {
  if (v === null || v === undefined) return "--";
  if (isCurrency) {
    // Use user's locale; change 'USD' if you want INR
    return v.toLocaleString(undefined, { style: "currency", currency: "USD", maximumFractionDigits: 2 });
  }
  if (typeof v === "number") return v.toLocaleString();
  return v;
}

export default function KpiCard({ title, value, subtitle, isCurrency = false }) {
  return (
    <div className="kpi-card">
      <div className="flex items-baseline justify-between">
        <h3 className="text-sm font-medium text-gray-500">{title}</h3>
        <div className="text-xs text-gray-400">{subtitle}</div>
      </div>
      <div className="mt-3">
        <div className="text-2xl font-semibold">{formatNumber(value, isCurrency)}</div>
      </div>
    </div>
  );
}
