import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import ChartEmpty from "../charts/ChartEmpty";
import { progression, careerSymbolSizes } from "../../lib/athletes";
import { useChartColors } from "../../lib/chart-colors";
import type { AthleteHistoryRow } from "../../lib/types";

export default function AthleteProgression({ history }: { history: AthleteHistoryRow[] }) {
  const colors = useChartColors();
  const pts = progression(history).filter((p) => p.pct != null);
  if (pts.length < 2)
    return <ChartEmpty height={260}>資料不足,無法畫進步曲線</ChartEmpty>;

  const sizes = careerSymbolSizes(pts.map((p) => p.races));
  const bestIdx = pts.reduce((bi, p, i) => ((p.pct as number) > (pts[bi].pct as number) ? i : bi), 0);

  const option: EChartsOption = {
    grid: { left: 48, right: 48, top: 32, bottom: 36 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const first = Array.isArray(p) ? p[0] : p;
        const idx = first?.dataIndex;
        if (idx == null || !pts[idx]) return "";
        return `${pts[idx].y} 年<br/>最佳場次贏過 ${pts[idx].pct}%<br/>出賽 ${pts[idx].races} 場`;
      },
    },
    xAxis: { type: "category", data: pts.map((p) => String(p.y)) },
    yAxis: { type: "value", name: "勝過%", min: 0, max: 100, axisLabel: { formatter: "{value}%" } },
    series: [{
      name: "最佳同場勝過%", type: "line", smooth: 0.4,
      symbol: "circle",
      symbolSize: (_: unknown, params: { dataIndex: number }) => sizes[params.dataIndex],
      lineStyle: { color: colors.accent, width: 2 },
      itemStyle: { color: colors.accent },
      areaStyle: { color: colors.accent, opacity: 0.15 },
      data: pts.map((p) => p.pct),
      markLine: {
        symbol: "none",
        data: [{ xAxis: String(pts[bestIdx].y),
          label: { formatter: "生涯最佳", color: colors.ink, position: "insideEndTop" as const },
          lineStyle: { color: colors.secondary, type: "dashed" as const } }],
      },
    }],
  };
  return <EChart option={option} height={260} />;
}
