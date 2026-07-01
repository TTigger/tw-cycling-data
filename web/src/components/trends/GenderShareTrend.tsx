import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import ChartEmpty from "../charts/ChartEmpty";
import type { GenderTrend } from "../../lib/overview";
import { useChartColors } from "../../lib/chart-colors";

const MIN_KNOWN = 30; // years with fewer known-gender finishers are not plotted

export default function GenderShareTrend({ gt }: { gt: GenderTrend }) {
  const colors = useChartColors();
  const pts = gt.years.map((y, i) =>
    gt.known[i] >= MIN_KNOWN ? Math.round((100 * gt.f[i]) / gt.known[i]) : null);
  if (pts.every((p) => p == null)) return <ChartEmpty height={260}>已知性別樣本不足</ChartEmpty>;
  const option: EChartsOption = {
    grid: { left: 44, right: 16, top: 24, bottom: 32 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const i = p[0].dataIndex;
        return p[0].value == null ? `${gt.years[i]}:樣本不足`
          : `${gt.years[i]}:女性 ${p[0].value}%(${gt.f[i]}/${gt.known[i]})`;
      },
    },
    xAxis: { type: "category", data: gt.years.map(String) },
    yAxis: { type: "value", name: "女性 %", max: 100, axisLabel: { formatter: "{value}%" } },
    series: [{ name: "女性比例", type: "line", smooth: true, connectNulls: false,
      itemStyle: { color: colors.accent }, data: pts }],
  };
  return <EChart option={option} height={260} />;
}
