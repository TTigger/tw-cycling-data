import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import ChartEmpty from "./ChartEmpty";
import { secondsToHMS } from "../../lib/format";
import type { CrossYearPoint } from "../../lib/overview";

/** Cross-year finish-time evolution for ONE race: median line + P25–P75 band
 * (drawn as a transparent P25 baseline + stacked filled range) + winner line.
 * Shared by the race page and the /trends page. */
export default function FinishTimeBand({ cy }: { cy: CrossYearPoint[] }) {
  if (cy.length < 2) return <ChartEmpty height={260}>僅單一年度,無跨年比較</ChartEmpty>;
  const years = cy.map((c) => String(c.y));
  const option: EChartsOption = {
    grid: { left: 64, right: 16, top: 24, bottom: 40 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const c = cy[p[0].dataIndex];
        return `${c.y}（${c.n} 人）<br/>冠軍 ${secondsToHMS(c.winner)}`
          + `<br/>中位 ${secondsToHMS(c.median)}`
          + `<br/>P25–P75 ${secondsToHMS(c.p25)} – ${secondsToHMS(c.p75)}`;
      },
    },
    legend: { bottom: 0, data: ["冠軍", "中位"] },
    xAxis: { type: "category", data: years },
    yAxis: { type: "value", name: "完賽時間", axisLabel: { formatter: (v: number) => secondsToHMS(v) } },
    series: [
      // P25 baseline (invisible) + range area to P75 — stacked so the fill spans P25..P75
      { name: "_p25", type: "line", stack: "band", symbol: "none", lineStyle: { opacity: 0 },
        data: cy.map((c) => c.p25), tooltip: { show: false }, silent: true },
      { name: "P25–P75", type: "line", stack: "band", symbol: "none", lineStyle: { opacity: 0 },
        areaStyle: { color: "#5B7B8A", opacity: 0.18 },
        data: cy.map((c) => c.p75 - c.p25), tooltip: { show: false }, silent: true },
      { name: "中位", type: "line", smooth: true, symbol: "circle",
        itemStyle: { color: "#5B7B8A" }, data: cy.map((c) => c.median) },
      { name: "冠軍", type: "line", smooth: true, symbol: "circle",
        itemStyle: { color: "#D97757" }, data: cy.map((c) => c.winner) },
    ],
  };
  return <EChart option={option} height={260} />;
}
