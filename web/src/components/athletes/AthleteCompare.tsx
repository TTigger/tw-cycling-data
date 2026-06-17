import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { careerSummary, progression } from "../../lib/athletes";
import { compareAthletes } from "../../lib/compare";
import { secondsToHMS } from "../../lib/format";
import type { AthleteDetail } from "../../lib/types";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");
const TRAIT_LABELS: Record<string, string> = { climb: "爬坡", road: "公路", crit: "繞圈", tt: "計時" };
const TRAIT_ORDER = ["climb", "road", "crit", "tt"];
const A_COLOR = "#D97757";
const B_COLOR = "#5B7B8A";

function StatRow({ label, a, b }: { label: string; a: string | number; b: string | number }) {
  return (
    <tr className="border-t border-border/60">
      <td className="py-1.5 num text-right text-accent">{a}</td>
      <td className="py-1.5 text-center text-xs text-muted">{label}</td>
      <td className="py-1.5 num" style={{ color: B_COLOR }}>{b}</td>
    </tr>
  );
}

export default function AthleteCompare(
  { a, b, onBack }: { a: AthleteDetail; b: AthleteDetail; onBack: () => void },
) {
  const cmp = compareAthletes(a, b);
  const sa = careerSummary(a), sb = careerSummary(b);

  // traits radar — axes = trait types either rider has
  const types = TRAIT_ORDER.filter((t) => a.traits[t] || b.traits[t]);
  const radar: EChartsOption | null = types.length >= 3 ? {
    radar: {
      indicator: types.map((t) => ({ name: TRAIT_LABELS[t], max: 100 })),
      radius: "62%", axisName: { color: "#6B6760", fontSize: 11 },
      splitLine: { lineStyle: { color: "#E8E3D9" } },
      splitArea: { areaStyle: { color: ["rgba(0,0,0,0)", "rgba(217,119,87,0.04)"] } },
    },
    legend: { bottom: 0, data: [a.nm, b.nm] },
    color: [A_COLOR, B_COLOR],
    tooltip: { trigger: "item" },
    series: [{
      type: "radar", areaStyle: { opacity: 0.12 }, lineStyle: { width: 2 },
      data: [
        { name: a.nm, value: types.map((t) => a.traits[t]?.pct ?? 0) },
        { name: b.nm, value: types.map((t) => b.traits[t]?.pct ?? 0) },
      ],
    }],
  } : null;

  // progression overlay — best in-field percentile per year
  const pa = progression(a.history).filter((p) => p.pct != null);
  const pb = progression(b.history).filter((p) => p.pct != null);
  const years = [...new Set([...pa, ...pb].map((p) => p.y))].sort((x, y) => x - y);
  const trend: EChartsOption | null = years.length >= 2 ? {
    grid: { left: 44, right: 16, top: 28, bottom: 36 },
    legend: { top: 0, data: [a.nm, b.nm] },
    color: [A_COLOR, B_COLOR],
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: years.map(String) },
    yAxis: { type: "value", min: 0, max: 100, name: "勝過%", axisLabel: { formatter: "{value}%" } },
    series: [a, b].map((_, i) => {
      const pts = i === 0 ? pa : pb;
      const by = new Map(pts.map((p) => [p.y, p.pct]));
      return {
        name: i === 0 ? a.nm : b.nm, type: "line", smooth: true, connectNulls: true,
        data: years.map((y) => by.get(y) ?? null),
      };
    }),
  } : null;

  const lead = cmp.aWins > cmp.bWins ? A_COLOR : cmp.aWins < cmp.bWins ? B_COLOR : "#6B6760";

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3">
        <h1 className="font-display text-2xl text-ink">
          <span className="text-accent">{a.nm}</span>
          <span className="mx-2 text-muted">vs</span>
          <span style={{ color: B_COLOR }}>{b.nm}</span>
        </h1>
        <button className="shrink-0 rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-accent"
          onClick={onBack}>← 返回</button>
      </div>

      <section className="rounded-xl border border-border bg-surface p-4 text-center">
        <div className="text-sm text-muted">同場交手戰績</div>
        <div className="mt-1 font-display text-3xl" style={{ color: lead }}>
          <span className="text-accent">{cmp.aWins}</span>
          <span className="mx-2 text-muted">–</span>
          <span style={{ color: B_COLOR }}>{cmp.bWins}</span>
        </div>
        <div className="text-xs text-muted">共 {cmp.meets} 場同場較勁{cmp.meets > cmp.aWins + cmp.bWins ? `(含 ${cmp.meets - cmp.aWins - cmp.bWins} 場同名次)` : ""}</div>
        <div className="mt-1 text-xs text-muted">以雙方每場每年最佳成績比較;名次較前者勝(與「宿敵」欄位的逐組計法略有不同)。</div>
      </section>

      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="mb-2 font-display text-lg text-ink">生涯數據</h2>
        <table className="w-full text-sm">
          <tbody>
            <StatRow label="出賽場次" a={sa.races} b={sb.races} />
            <StatRow label="涵蓋年數" a={sa.years} b={sb.years} />
            <StatRow label="冠軍" a={sa.wins} b={sb.wins} />
            <StatRow label="前三名" a={sa.podiums} b={sb.podiums} />
            <StatRow label="最佳名次" a={sa.bestRank ?? "—"} b={sb.bestRank ?? "—"} />
          </tbody>
        </table>
      </section>

      {radar && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="font-display text-lg text-ink">專長雷達疊圖</h2>
          <p className="mb-2 text-xs text-muted">各賽事類型「贏過全場 %」中位數。</p>
          <EChart option={radar} height={300} />
        </section>
      )}

      {trend && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="font-display text-lg text-ink">進步軌跡疊圖</h2>
          <p className="mb-2 text-xs text-muted">每年最佳「同場贏過 %」,跨賽事可比。</p>
          <EChart option={trend} height={260} />
        </section>
      )}

      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="font-display text-lg text-ink">同場較勁明細</h2>
        {cmp.common.length === 0 ? (
          <p className="mt-2 text-sm text-muted">兩人沒有同場出賽紀錄。</p>
        ) : (
          <div className="mt-2 overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted">
                  <th className="py-1 pr-3">年</th><th className="py-1 pr-3">賽事</th>
                  <th className="py-1 pr-3 num text-accent">{a.nm}</th>
                  <th className="py-1 pr-3 num" style={{ color: B_COLOR }}>{b.nm}</th>
                  <th className="py-1 pr-3">勝</th>
                </tr>
              </thead>
              <tbody>
                {cmp.common.map((r, i) => (
                  <tr key={i} className="border-t border-border/60">
                    <td className="py-1.5 pr-3 num text-muted">{r.y}</td>
                    <td className="py-1.5 pr-3">
                      <a className="text-ink hover:text-accent"
                        href={`${base}/race?rk=${encodeURIComponent(r.rk)}&y=${r.y}`}>{r.rn}</a>
                    </td>
                    <td className="py-1.5 pr-3 num text-muted">
                      {r.aRank ?? "—"}<span className="ml-1 text-xs text-muted">({secondsToHMS(r.aT)})</span>
                    </td>
                    <td className="py-1.5 pr-3 num text-muted">
                      {r.bRank ?? "—"}<span className="ml-1 text-xs text-muted">({secondsToHMS(r.bT)})</span>
                    </td>
                    <td className="py-1.5 pr-3">
                      {r.winner === "a" ? <span className="text-accent">◀ {a.nm}</span>
                        : r.winner === "b" ? <span style={{ color: B_COLOR }}>{b.nm} ▶</span>
                        : <span className="text-muted">平</span>}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
