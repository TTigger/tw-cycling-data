import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import ChartEmpty from "../charts/ChartEmpty";
import { useChartColors } from "../../lib/chart-colors";
import type { Composition } from "../../lib/overview";

export default function CompositionByClass({ composition: c }: { composition: Composition }) {
  const colors = useChartColors();
  if (!c.classes.length) return <ChartEmpty height={300}>無資料</ChartEmpty>;
  const option: EChartsOption = {
    grid: { left: 56, right: 16, top: 16, bottom: 64 },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { bottom: 0 },
    xAxis: { type: "category", data: c.classes, axisLabel: { rotate: 30 } },
    yAxis: { type: "value", name: "人次" },
    series: [
      { name: "男", type: "bar", stack: "g", data: c.male, itemStyle: { color: colors.secondary } },
      { name: "女", type: "bar", stack: "g", data: c.female, itemStyle: { color: colors.accent } },
      { name: "未標示", type: "bar", stack: "g", data: c.unknown, itemStyle: { color: colors.muted } },
    ],
  };
  return <EChart option={option} height={300} />;
}
