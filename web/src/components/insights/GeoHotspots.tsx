import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import type { GeoRegion } from "../../lib/types";
import { useChartColors } from "../../lib/chart-colors";

export default function GeoHotspots({ regions }: { regions: GeoRegion[] }) {
  const colors = useChartColors();
  if (!regions.length) return <p className="text-muted">無資料</p>;
  const top = [...regions].slice(0, 15).reverse();   // ECharts y-axis bottom-up
  const option: EChartsOption = {
    grid: { left: 56, right: 64, top: 12, bottom: 24 },
    tooltip: {
      trigger: "axis",
      formatter: (p: any) => {
        const r = top[p[0].dataIndex];
        return `${r.region}<br/>${r.rows.toLocaleString()} 人次 · ${r.races} 場賽事`;
      },
    },
    xAxis: { type: "value", name: "人次" },
    yAxis: { type: "category", data: top.map((r) => r.region) },
    series: [{
      type: "bar", data: top.map((r) => r.rows), barWidth: "62%",
      itemStyle: { color: colors.accent },
      label: { show: true, position: "right",
        formatter: (p: any) => top[p.dataIndex].races + " 場" },
    }],
  };
  return (
    <div>
      <EChart option={option} height={Math.max(260, top.length * 26)} />
      <p className="mt-2 text-xs text-muted">
        以賽事名稱中的地名(輔以來源 region 欄位)歸縣市;長度為人次,標籤為賽事場數。武嶺相關賽事使南投人次居首。
      </p>
    </div>
  );
}
