import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import ChartEmpty from "../charts/ChartEmpty";
import { secondsToHMS } from "../../lib/format";

export default function CrossYearTrend({ cy }: { cy: { y: number; winner: number; median: number }[] }) {
  if (cy.length < 2) return <ChartEmpty height={260}>僅單一年度,無跨年比較</ChartEmpty>;
  const option: EChartsOption = {
    grid: { left: 64, right: 16, top: 24, bottom: 40 },
    tooltip: { trigger: "axis", formatter: (p: any) =>
      p.map((s: any) => `${s.seriesName} ${secondsToHMS(s.value)}`).join("<br/>") },
    legend: { bottom: 0 },
    xAxis: { type: "category", data: cy.map((c) => String(c.y)) },
    yAxis: { type: "value", name: "完賽時間", axisLabel: { formatter: (v: number) => secondsToHMS(v) } },
    series: [
      { name: "冠軍", type: "line", data: cy.map((c) => c.winner), itemStyle: { color: "#D97757" }, smooth: true },
      { name: "中位", type: "line", data: cy.map((c) => c.median), itemStyle: { color: "#5B7B8A" }, smooth: true },
    ],
  };
  return <EChart option={option} height={260} />;
}
