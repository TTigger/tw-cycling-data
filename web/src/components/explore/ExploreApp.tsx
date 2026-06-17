import { useEffect, useMemo, useState } from "react";
import { useStore } from "@nanostores/react";
import "../../lib/echarts-theme";
import { loadViz, loadRaces } from "../../lib/data-load";
import { $filters, applyFilters, hydrateFromUrl } from "../../lib/filter-store";
import { facetOptions } from "../../lib/aggregate";
import type { SlimRecord, RaceIndex } from "../../lib/types";
import FilterBar from "./FilterBar";
import FinishTimeHistogram from "../charts/FinishTimeHistogram";
import AgeBoxplot from "../charts/AgeBoxplot";
import CompetitivenessSpread from "../charts/CompetitivenessSpread";
import DistanceSpeedScatter from "../charts/DistanceSpeedScatter";
import Skeleton from "../Skeleton";

function Card({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">{title}</h2>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}

export default function ExploreApp() {
  const [viz, setViz] = useState<SlimRecord[] | null>(null);
  const [races, setRaces] = useState<RaceIndex[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const f = useStore($filters);

  useEffect(() => {
    hydrateFromUrl();
    Promise.all([loadViz(), loadRaces()])
      .then(([v, r]) => { setViz(v); setRaces(r); })
      .catch((e) => setErr(String(e)));
  }, []);

  const facets = useMemo(() => (viz ? facetOptions(viz) : null), [viz]);
  const filtered = useMemo(() => (viz ? applyFilters(viz, f) : []), [viz, f]);
  const nameMap = useMemo(() => new Map(races.map((r) => [r.rk, r.rn])), [races]);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!viz || !facets) return <Skeleton cards={4} />;

  return (
    <div className="space-y-6">
      <FilterBar facets={facets} races={races} />
      <p className="text-sm text-muted">
        符合條件:<span className="num text-ink">{filtered.length.toLocaleString()}</span> 筆
      </p>
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="完賽時間分布" hint="每 10 分鐘一桶"><FinishTimeHistogram rows={filtered} /></Card>
        <Card title="分齡組 vs 完賽時間" hint="點組別可篩選 · 僅競技型賽事有分齡"><AgeBoxplot rows={filtered} /></Card>
        <Card title="賽事競爭強度(中位/冠軍 倍數)" hint="點賽事可篩選 · 已排除認證型"><CompetitivenessSpread rows={filtered} nameMap={nameMap} /></Card>
        <Card title="距離 vs 平均速度" hint="距離可解析者約 48%"><DistanceSpeedScatter rows={filtered} /></Card>
      </div>
    </div>
  );
}
