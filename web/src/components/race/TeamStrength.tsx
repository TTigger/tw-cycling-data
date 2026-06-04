import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { teamStrength } from "../../lib/racedetail";
import type { DetailRow } from "../../lib/types";

export default function TeamStrength({ rows }: { rows: DetailRow[] }) {
  const teams = teamStrength(rows, 12, 10);
  if (!teams.length) return <div className="flex h-[300px] items-center justify-center text-muted">無車隊資料</div>;
  const option: EChartsOption = {
    grid: { left: 160, right: 24, top: 16, bottom: 32 },
    tooltip: { trigger: "item", formatter: (p: any) => {
      const t = teams[p.dataIndex]; return `${t.team}<br/>前 10 名 ${t.top} 次<br/>領獎台 ${t.podium} 次`; } },
    xAxis: { type: "value", name: "前 10 名人次" },
    yAxis: { type: "category", inverse: true, data: teams.map((t) => t.team),
      axisLabel: { width: 150, overflow: "truncate" } },
    series: [{ type: "bar", data: teams.map((t) => t.top), itemStyle: { color: "#7C8C6B" }, barWidth: "70%" }],
  };
  return <EChart option={option} height={300} />;
}
