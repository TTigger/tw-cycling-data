import { useEffect, useMemo, useState } from "react";
import "../../lib/echarts-theme";
import { loadViz } from "../../lib/data-load";
import { kpiStats } from "../../lib/overview";
import type { SlimRecord } from "../../lib/types";
import KpiCards from "./KpiCards";
import SeasonHeatmap from "./SeasonHeatmap";
import ParticipationTrend from "./ParticipationTrend";
import WomenParticipation from "./WomenParticipation";
import CompositionByClass from "./CompositionByClass";

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
  const [viz, setViz] = useState<SlimRecord[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    loadViz().then(setViz).catch((e) => setErr(String(e)));
  }, []);

  const kpi = useMemo(() => (viz ? kpiStats(viz) : null), [viz]);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!viz || !kpi) return <p className="text-muted">載入中…</p>;

  return (
    <div className="space-y-6">
      <KpiCards kpi={kpi} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="賽季行事曆" hint="各月份人次(date 100% 完整)"><SeasonHeatmap rows={viz} /></Card>
        <Card title="逐年參賽趨勢" hint="依系列堆疊(前 8 大)"><ParticipationTrend rows={viz} /></Card>
        <Card title="女子參與度" hint="各系列女子佔比 · 樣本≥50"><WomenParticipation rows={viz} /></Card>
        <Card title="組別 / 性別組成" hint="「未標示」多為市民賽不分組"><CompositionByClass rows={viz} /></Card>
      </div>
    </div>
  );
}
