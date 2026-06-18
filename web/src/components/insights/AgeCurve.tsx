import { useMemo, useState } from "react";
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import type { AgeCurvePoint } from "../../lib/types";

const ORDER = ["U19", "19-29", "30-39", "40-49", "50-59", "60+"];

export default function AgeCurve({ points }: { points: AgeCurvePoint[] }) {
  const [g, setG] = useState<"all" | "M" | "F">("all");
  const rows = useMemo(
    () => ORDER.map((b) => points.find((p) => p.band === b && p.g === g)).filter(Boolean) as AgeCurvePoint[],
    [points, g],
  );

  if (rows.length < 2)
    return <div className="flex h-[300px] items-center justify-center text-muted">此分組資料不足</div>;

  const bands = rows.map((r) => r.band);
  const option: EChartsOption = {
    grid: { left: 48, right: 16, top: 24, bottom: 36 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const r = rows[p[0].dataIndex];
        return `${r.band} 歲<br/>中位:贏過 ${r.p50}%<br/>四分位:${r.p25}–${r.p75}%<br/>樣本 ${r.n.toLocaleString()}`;
      },
    },
    xAxis: { type: "category", data: bands, name: "年齡層" },
    yAxis: { type: "value", name: "贏過全場 %", min: 0, max: 100, axisLabel: { formatter: "{value}%" } },
    series: [
      // p25 transparent base + (p75-p25) shaded band
      { name: "p25", type: "line", stack: "band", data: rows.map((r) => r.p25),
        lineStyle: { opacity: 0 }, symbol: "none", silent: true },
      { name: "iqr", type: "line", stack: "band", data: rows.map((r) => r.p75 - r.p25),
        lineStyle: { opacity: 0 }, symbol: "none", silent: true,
        areaStyle: { color: "rgba(217,119,87,0.12)" } },
      // p50 median line on top (not stacked)
      { name: "中位 %", type: "line", data: rows.map((r) => r.p50), smooth: true,
        itemStyle: { color: "#D97757" }, lineStyle: { width: 3 },
        label: { show: true, formatter: "{c}%", position: "top" } },
    ],
  };

  return (
    <div>
      <div className="mb-2 flex gap-2 text-sm">
        {([["all", "全部"], ["M", "男"], ["F", "女"]] as const).map(([v, t]) => (
          <button key={v} onClick={() => setG(v)}
            className={`rounded-lg border px-2 py-1 ${g === v ? "border-accent text-accent" : "border-border text-muted hover:text-accent"}`}>
            {t}
          </button>
        ))}
      </div>
      <EChart option={option} height={300} />
      <p className="mt-2 text-xs text-muted">
        每筆成績的「贏過全場 %」=(完賽人數−名次)/完賽人數,按選手該場年齡層彙整(中位數,陰影為四分位距)。
        年齡層為十年制粗分;存在倖存者偏差(僅持續參賽的選手會留在較年長分組),屬探索性觀察,非生理巔峰推論。
      </p>
    </div>
  );
}
