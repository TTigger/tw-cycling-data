import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import type { WomenShare } from "../../lib/overview";

export default function WomenParticipation({ women }: { women: WomenShare[] }) {
  const shares = women.slice(0, 12);
  if (!shares.length) return <div className="flex h-[320px] items-center justify-center text-muted">無足夠性別資料</div>;
  const option: EChartsOption = {
    grid: { left: 170, right: 32, top: 16, bottom: 32 },
    tooltip: {
      trigger: "item",
      formatter: (p: any) => { const w = shares[p.dataIndex]; return `${w.series}<br/>女子 ${w.f}/${w.total}(${w.pct}%)`; },
    },
    xAxis: { type: "value", name: "女子 %" },
    yAxis: { type: "category", inverse: true, data: shares.map((w) => w.series),
      axisLabel: { width: 160, overflow: "truncate" } },
    series: [{ type: "bar", data: shares.map((w) => w.pct), itemStyle: { color: "#9A7AA0" }, barWidth: "70%",
      label: { show: true, position: "right", formatter: "{c}%", color: "#6B6760" } }],
  };
  return <EChart option={option} height={320} />;
}
