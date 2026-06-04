import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { compositionByClass } from "../../lib/overview";
import type { SlimRecord } from "../../lib/types";

export default function CompositionByClass({ rows }: { rows: SlimRecord[] }) {
  const c = compositionByClass(rows);
  if (!c.classes.length) return <div className="flex h-[300px] items-center justify-center text-muted">無資料</div>;
  const option: EChartsOption = {
    grid: { left: 56, right: 16, top: 16, bottom: 64 },
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { bottom: 0, textStyle: { color: "#6B6760" } },
    xAxis: { type: "category", data: c.classes, axisLabel: { rotate: 30 } },
    yAxis: { type: "value", name: "人次" },
    series: [
      { name: "男", type: "bar", stack: "g", data: c.male, itemStyle: { color: "#5B7B8A" } },
      { name: "女", type: "bar", stack: "g", data: c.female, itemStyle: { color: "#D97757" } },
      { name: "未標示", type: "bar", stack: "g", data: c.unknown, itemStyle: { color: "#C9C2B5" } },
    ],
  };
  return <EChart option={option} height={300} />;
}
