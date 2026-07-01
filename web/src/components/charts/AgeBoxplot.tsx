import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import ChartEmpty from "./ChartEmpty";
import { boxByGroup } from "../../lib/aggregate";
import { secondsToHMS } from "../../lib/format";
import { setFilter } from "../../lib/filter-store";
import { useChartColors } from "../../lib/chart-colors";
import type { SlimRecord } from "../../lib/types";

export default function AgeBoxplot({ rows }: { rows: SlimRecord[] }) {
  const colors = useChartColors();
  const boxes = boxByGroup(rows.map((r) => ({ ag: r.ag, t: r.t })), 8);
  if (!boxes.length) {
    return <ChartEmpty height={320}>此條件下無分齡資料(僅競技型賽事有分齡組)</ChartEmpty>;
  }
  const option: EChartsOption = {
    grid: { left: 64, right: 16, top: 24, bottom: 40 },
    tooltip: {
      trigger: "item",
      formatter: (p: any) => {
        const b = boxes[p.dataIndex];
        if (!b) return "";
        return `${b.group}(${b.n} 人)<br/>中位 ${secondsToHMS(b.median)}<br/>Q1 ${secondsToHMS(b.q1)} / Q3 ${secondsToHMS(b.q3)}`;
      },
    },
    xAxis: { type: "category", data: boxes.map((b) => b.group), axisLabel: { rotate: 45 } },
    yAxis: { type: "value", name: "完賽時間", axisLabel: { formatter: (v: number) => secondsToHMS(v) } },
    series: [{
      type: "boxplot",
      data: boxes.map((b) => [b.min, b.q1, b.median, b.q3, b.max]),
      itemStyle: { color: "transparent", borderColor: colors.accent },
    }],
  };
  const onEvents = {
    click: (p: any) => { const b = boxes[p.dataIndex]; if (b) setFilter("ageGroup", b.group); },
  };
  return <EChart option={option} onEvents={onEvents} />;
}
