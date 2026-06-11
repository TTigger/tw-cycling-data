import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { progression } from "../../lib/athletes";
import type { AthleteHistoryRow } from "../../lib/types";

export default function AthleteProgression({ history }: { history: AthleteHistoryRow[] }) {
  const pts = progression(history).filter((p) => p.pct != null);
  if (pts.length < 2)
    return <div className="flex h-[260px] items-center justify-center text-muted">資料不足,無法畫進步曲線</div>;

  const option: EChartsOption = {
    grid: { left: 48, right: 48, top: 24, bottom: 36 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const x = Array.isArray(p) ? p : [p];
        const y = x[0]?.axisValue;
        const pct = x.find((s: any) => s.seriesName === "最佳同場勝過%");
        const races = x.find((s: any) => s.seriesName === "出賽場次");
        return `${y} 年<br/>最佳場次贏過 ${pct?.value ?? "—"}%<br/>出賽 ${races?.value ?? "—"} 場`;
      },
    },
    xAxis: { type: "category", data: pts.map((p) => String(p.y)) },
    yAxis: [
      { type: "value", name: "勝過%", min: 0, max: 100, position: "left",
        axisLabel: { formatter: "{value}%" } },
      { type: "value", name: "場次", min: 0, position: "right", splitLine: { show: false } },
    ],
    series: [
      { name: "最佳同場勝過%", type: "line", smooth: true, yAxisIndex: 0,
        data: pts.map((p) => p.pct), itemStyle: { color: "#D97757" },
        areaStyle: { color: "rgba(217,119,87,0.10)" } },
      { name: "出賽場次", type: "bar", yAxisIndex: 1, barWidth: "36%",
        data: pts.map((p) => p.races), itemStyle: { color: "rgba(91,123,138,0.45)" } },
    ],
  };
  return <EChart option={option} height={260} />;
}
