import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import ChartEmpty from "./ChartEmpty";
import { densityRidge } from "../../lib/aggregate";
import { secondsToHMS } from "../../lib/format";
import { useChartColors } from "../../lib/chart-colors";

export interface RidgeMarker { value: number; label: string; color?: string; }

/** Finish-time distribution as a smooth density ridge (accent line + faint fill),
 * with optional vertical markers (median / winner / your time). Theme-aware. */
export default function DistributionRidge({
  values, markers = [], height = 280, binWidth = 300,
}: { values: number[]; markers?: RidgeMarker[]; height?: number; binWidth?: number }) {
  const colors = useChartColors();
  const pts = densityRidge(values, binWidth);
  if (!pts.length) return <ChartEmpty height={height}>無時間資料</ChartEmpty>;
  const option: EChartsOption = {
    grid: { left: 48, right: 16, top: 24, bottom: 40 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const pt = Array.isArray(p) ? p[0] : p;
        if (!pt || !pt.value) return "";
        return `${secondsToHMS(pt.value[0])}<br/>${pt.value[1]} 人`;
      },
    },
    xAxis: { type: "value", axisLabel: { formatter: (v: number) => secondsToHMS(v) } },
    yAxis: { type: "value", name: "人數" },
    series: [{
      type: "line", smooth: 0.4, symbol: "none", data: pts,
      lineStyle: { color: colors.accent, width: 2 },
      areaStyle: { color: colors.accent, opacity: 0.15 },
      markLine: markers.length ? {
        symbol: "none",
        data: markers.map((m) => ({
          xAxis: m.value,
          label: { formatter: m.label, color: colors.ink, position: "insideEndTop" as const },
          lineStyle: { color: m.color ?? colors.secondary, type: "dashed" as const },
        })),
      } : undefined,
    }],
  };
  return <EChart option={option} height={height} />;
}
