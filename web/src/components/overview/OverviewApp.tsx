import { useEffect, useState } from "react";
import "../../lib/echarts-theme";
import { loadOverview } from "../../lib/data-load";
import type { OverviewData } from "../../lib/overview";
import KpiCards from "./KpiCards";
import SeasonHeatmap from "./SeasonHeatmap";
import ParticipationTrend from "./ParticipationTrend";
import WomenParticipation from "./WomenParticipation";
import CompositionByClass from "./CompositionByClass";
import Skeleton from "../Skeleton";
import Favorites from "../Favorites";

function Card({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">{title}</h2>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}

export default function OverviewApp() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    loadOverview().then(setData).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!data) return <Skeleton cards={4} />;

  return (
    <div className="space-y-6">
      <Favorites />
      <KpiCards kpi={data.kpi} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="賽季行事曆" hint="各月份人次(date 100% 完整)"><SeasonHeatmap heat={data.heat} /></Card>
        <Card title="逐年參賽趨勢" hint="依系列堆疊(前 8 大)"><ParticipationTrend trend={data.trend} /></Card>
        <Card title="女子參與度" hint="各系列女子佔比 · 樣本≥50"><WomenParticipation women={data.women} /></Card>
        <Card title="組別 / 性別組成" hint="「未標示」多為市民賽不分組"><CompositionByClass composition={data.composition} /></Card>
      </div>
    </div>
  );
}
