import { useEffect, useState } from "react";
import "../../lib/echarts-theme";
import { loadInsights } from "../../lib/data-load";
import type { Insights } from "../../lib/types";
import AgeCurve from "./AgeCurve";
import Breakout from "./Breakout";
import RaceRatings from "./RaceRatings";

function Card({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">{title}</h2>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}

export default function InsightsApp() {
  const [ins, setIns] = useState<Insights | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    loadInsights().then(setIns).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!ins) return <p className="text-muted">載入中…</p>;

  return (
    <div className="space-y-6">
      <Card title="年齡 vs 全場表現" hint="各年齡層在全場的相對名次落點(跨賽事正規化)">
        <AgeCurve points={ins.age_curve} />
      </Card>
      <Card title="🚀 突破之星" hint="年度間相對表現躍升最大的選手">
        <Breakout entries={ins.breakout} />
      </Card>
      <Card title="⭐ 賽事星等" hint="規模 × 屆數 × 場域深度的綜合競爭力評分">
        <RaceRatings ratings={ins.ratings} />
      </Card>
    </div>
  );
}
