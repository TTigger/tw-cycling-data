import type { Kpi } from "../../lib/overview";

function Card({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-4">
      <div className="text-sm text-muted">{label}</div>
      <div className="num text-3xl text-ink">{value}</div>
    </div>
  );
}

export default function KpiCards({ kpi }: { kpi: Kpi }) {
  const years = kpi.minYear != null && kpi.maxYear != null
    ? (kpi.minYear === kpi.maxYear ? String(kpi.minYear) : `${kpi.minYear}–${String(kpi.maxYear).slice(2)}`)
    : "—";
  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
      <Card label="成績筆數" value={kpi.records.toLocaleString()} />
      <Card label="賽事" value={String(kpi.races)} />
      <Card label="系列" value={String(kpi.series)} />
      <Card label="年份" value={years} />
    </div>
  );
}
