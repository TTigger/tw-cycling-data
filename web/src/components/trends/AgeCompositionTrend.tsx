import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import ChartEmpty from "../charts/ChartEmpty";
import type { AgeTrend } from "../../lib/overview";

const COLORS = ["#9CC3D5", "#5B7B8A", "#7FB069", "#E6B05E", "#D97757", "#8E6C88"];

export default function AgeCompositionTrend({ at }: { at: AgeTrend }) {
  if (!at.years.length) return <ChartEmpty height={260}>無分齡資料</ChartEmpty>;
  const option: EChartsOption = {
    grid: { left: 44, right: 16, top: 24, bottom: 48 },
    tooltip: { trigger: "axis" },
    legend: { bottom: 0 },
    xAxis: { type: "category", data: at.years.map(String) },
    yAxis: { type: "value", name: "% (分齡者)", max: 100, axisLabel: { formatter: "{value}%" } },
    series: at.bands.map((b, bi) => ({
      name: b, type: "line", stack: "age", areaStyle: { opacity: 0.7 }, symbol: "none",
      itemStyle: { color: COLORS[bi % COLORS.length] }, data: at.pct[bi],
    })),
  };
  return <EChart option={option} height={260} />;
}
