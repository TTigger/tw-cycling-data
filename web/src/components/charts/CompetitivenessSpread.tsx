import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import ChartEmpty from "./ChartEmpty";
import { raceSpread } from "../../lib/aggregate";
import { setFilter } from "../../lib/filter-store";
import type { SlimRecord } from "../../lib/types";

export default function CompetitivenessSpread(
  { rows, nameMap }: { rows: SlimRecord[]; nameMap: Map<string, string> },
) {
  const spreads = raceSpread(rows.map((r) => ({ rk: r.rk, y: r.y, t: r.t, rc: r.rc, s: r.s })), 10).slice(0, 15);
  if (!spreads.length) return <ChartEmpty height={360}>此條件下無足夠資料</ChartEmpty>;
  const labels = spreads.map((s) => `${nameMap.get(s.rk) ?? s.rk} ${s.y ?? ""}`.trim());
  const option: EChartsOption = {
    grid: { left: 200, right: 24, top: 24, bottom: 40 },
    tooltip: {
      trigger: "item",
      formatter: (p: any) => {
        const s = spreads[p.dataIndex];
        return `${labels[p.dataIndex]}<br/>離散倍數 ${s.ratio.toFixed(2)}×(中位/冠軍)<br/>${s.n} 人`;
      },
    },
    xAxis: { type: "value", name: "中位/冠軍 倍數" },
    yAxis: { type: "category", data: labels, inverse: true, axisLabel: { width: 190, overflow: "truncate" } },
    series: [{ type: "bar", data: spreads.map((s) => Number(s.ratio.toFixed(2))), itemStyle: { color: "#5B7B8A" }, barWidth: "70%" }],
  };
  const onEvents = { click: (p: any) => { const s = spreads[p.dataIndex]; if (s) setFilter("race", s.rk); } };
  return <EChart option={option} height={360} onEvents={onEvents} />;
}
