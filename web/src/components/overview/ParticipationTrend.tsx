import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { trendByYearSeries } from "../../lib/overview";
import type { SlimRecord } from "../../lib/types";

export default function ParticipationTrend({ rows }: { rows: SlimRecord[] }) {
  const t = trendByYearSeries(rows, 8);
  if (!t.years.length) return <div className="flex h-[300px] items-center justify-center text-muted">無資料</div>;
  const option: EChartsOption = {
    grid: { left: 56, right: 16, top: 16, bottom: 64 },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { type: "scroll", bottom: 0, textStyle: { color: "#6B6760" } },
    xAxis: { type: "category", data: t.years.map(String) },
    yAxis: { type: "value", name: "人次" },
    series: t.series.map((s) => ({ name: s, type: "bar", stack: "total", data: t.counts[s] })),
  };
  return <EChart option={option} height={300} />;
}
