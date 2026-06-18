import type { EChartsOption } from "echarts";
import EChart from "./EChart";
import ChartEmpty from "./ChartEmpty";
import { distSpeedPoints } from "../../lib/aggregate";
import type { SlimRecord } from "../../lib/types";

export default function DistanceSpeedScatter({ rows }: { rows: SlimRecord[] }) {
  const pts = distSpeedPoints(rows.map((r) => ({ dist: r.dist, spd: r.spd, rc: r.rc })));
  if (!pts.length) {
    return <ChartEmpty height={320}>此條件下無距離/速度資料(約涵蓋 48% 賽事)</ChartEmpty>;
  }
  const option: EChartsOption = {
    grid: { left: 56, right: 16, top: 24, bottom: 44 },
    tooltip: { trigger: "item", formatter: (p: any) => `${p.value[0]} km · ${p.value[1]} km/h` },
    xAxis: { type: "value", name: "距離 (km)", nameLocation: "middle", nameGap: 28 },
    yAxis: { type: "value", name: "平均速度 (km/h)" },
    series: [{
      type: "scatter", symbolSize: 6,
      data: pts.map((p) => [p.dist, p.spd]),
      itemStyle: { color: "rgba(217,119,87,0.5)" },
    }],
  };
  return <EChart option={option} />;
}
