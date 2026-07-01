import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import ChartEmpty from "../charts/ChartEmpty";
import { useChartColors } from "../../lib/chart-colors";
import type { Heat } from "../../lib/overview";

const MONTHS = Array.from({ length: 12 }, (_, i) => `${i + 1}月`);

export default function SeasonHeatmap({ heat }: { heat: Heat }) {
  const colors = useChartColors();
  if (!heat.cells.length) return <ChartEmpty height={260}>無資料</ChartEmpty>;
  const option: EChartsOption = {
    grid: { left: 56, right: 16, top: 16, bottom: 64 },
    tooltip: {
      position: "top",
      formatter: (p: any) => `${MONTHS[p.value[0]]} ${heat.years[p.value[1]]}<br/>${p.value[2].toLocaleString()} 人次`,
    },
    xAxis: { type: "category", data: MONTHS, splitArea: { show: true } },
    yAxis: { type: "category", data: heat.years.map(String), splitArea: { show: true } },
    visualMap: {
      min: 0, max: heat.max, calculable: true, orient: "horizontal", left: "center", bottom: 8,
      inRange: { color: colors.heat },
    },
    series: [{ type: "heatmap", data: heat.cells, label: { show: false },
      emphasis: { itemStyle: { borderColor: colors.ink, borderWidth: 1 } } }],
  };
  return <EChart option={option} height={260} />;
}
