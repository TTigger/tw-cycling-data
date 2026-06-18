import { useEffect, useMemo, useState } from "react";
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { loadRaceDifficulty } from "../../lib/data-load";
import { calibratableRaces, calibratedSeries } from "../../lib/difficulty";
import { secondsToHMS } from "../../lib/format";
import type { AthleteHistoryRow, RaceDifficultyFile } from "../../lib/types";

export default function CalibratedProgress({ history }: { history: AthleteHistoryRow[] }) {
  const [diffFile, setDiffFile] = useState<RaceDifficultyFile | null>(null);
  const [err, setErr] = useState(false);
  const [rk, setRk] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    loadRaceDifficulty()
      .then((d) => { if (live) setDiffFile(d); })
      .catch(() => { if (live) setErr(true); });
    return () => { live = false; };
  }, []);

  const races = useMemo(
    () => (diffFile ? calibratableRaces(history, diffFile) : []),
    [diffFile, history],
  );
  const activeRk = rk && races.some((r) => r.rk === rk) ? rk : races[0]?.rk ?? null;
  const series = useMemo(
    () => (diffFile && activeRk ? calibratedSeries(history, activeRk, diffFile[activeRk]) : []),
    [diffFile, activeRk, history],
  );

  if (err || (diffFile && races.length === 0)) return null; // nothing to calibrate

  const option: EChartsOption | null = series.length
    ? {
        grid: { left: 56, right: 16, top: 28, bottom: 36 },
        legend: { top: 0, right: 0, data: ["原始完賽", "難度校正後"] },
        tooltip: {
          trigger: "axis",
          formatter: (p: any) => {
            const x = Array.isArray(p) ? p : [p];
            const pt = series.find((s) => String(s.y) === String(x[0]?.axisValue));
            const lines = x.map((s: any) => `${s.marker}${s.seriesName}:${secondsToHMS(s.value)}`);
            const tag = pt ? (pt.coeff > 1 ? "偏難" : pt.coeff < 1 ? "偏易" : "持平") : "";
            return `${x[0]?.axisValue} 年<br/>${lines.join("<br/>")}<br/>難度係數 ${pt?.coeff ?? "—"}（${tag}）`;
          },
        },
        xAxis: { type: "category", data: series.map((s) => String(s.y)) },
        yAxis: {
          type: "value", scale: true, name: "完賽",
          axisLabel: { formatter: (v: number) => secondsToHMS(v) },
        },
        series: [
          { name: "原始完賽", type: "line", smooth: true, data: series.map((s) => s.raw),
            itemStyle: { color: "rgba(91,123,138,0.7)" }, lineStyle: { type: "dashed" } },
          { name: "難度校正後", type: "line", smooth: true, data: series.map((s) => s.calibrated),
            itemStyle: { color: "#D97757" }, areaStyle: { color: "rgba(217,119,87,0.10)" } },
        ],
      }
    : null;

  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">跨年難度校正</h2>
      <p className="mb-2 text-xs text-muted">
        每年完賽時間除以「難度係數」(該年中位數 ÷ 該賽事歷年中位數),排除「那年好騎/難騎」的影響,看絕對實力是否真的進步(校正後時間越低越好;僅供參考)。
      </p>
      {races.length > 1 && (
        <div className="mb-3 flex flex-wrap gap-2">
          {races.map((r) => (
            <button key={r.rk} onClick={() => setRk(r.rk)}
              className={`rounded-full border px-2.5 py-1 text-xs ${
                r.rk === activeRk ? "border-accent bg-accent/10 text-accent" : "border-border text-muted hover:border-accent"
              }`}>
              {r.name ?? r.rk}<span className="ml-1 num">{r.n}年</span>
            </button>
          ))}
        </div>
      )}
      {option ? <EChart option={option} height={260} /> : <p className="text-sm text-muted">計算中…</p>}
    </section>
  );
}
