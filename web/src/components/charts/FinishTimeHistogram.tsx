import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import ChartEmpty from "./ChartEmpty";
import { histogram } from "../../lib/aggregate";
import { secondsToHMS } from "../../lib/format";
import { useChartColors } from "../../lib/chart-colors";
import type { SlimRecord } from "../../lib/types";

const BIN = 600; // 10-minute buckets

export default function FinishTimeHistogram({ rows }: { rows: SlimRecord[] }) {
  const colors = useChartColors();
  const values = rows.map((r) => r.t).filter((t): t is number => t != null);
  const bins = histogram(values, BIN);
  if (!bins.length) {
    return <ChartEmpty height={320}>此條件下無資料</ChartEmpty>;
  }
  const option: EChartsOption = {
    grid: { left: 48, right: 16, top: 24, bottom: 40 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const b = bins[p[0].dataIndex];
        if (!b) return "";
        return `${secondsToHMS(b.x0)}–${secondsToHMS(b.x1)}<br/>${p[0].value} 人`;
      },
    },
    xAxis: {
      type: "category",
      data: bins.map((b) => secondsToHMS(b.x0)),
      axisLabel: { interval: Math.max(0, Math.floor(bins.length / 8)) },
    },
    yAxis: { type: "value", name: "人數" },
    series: [{ type: "bar", data: bins.map((b) => b.count), itemStyle: { color: colors.accent }, barWidth: "90%" }],
  };
  return <EChart option={option} />;
}
