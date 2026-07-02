import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import ChartEmpty from "../charts/ChartEmpty";
import type { AgeTrend } from "../../lib/overview";
import { joyRidges } from "../../lib/joyplot";
import { useChartColors } from "../../lib/chart-colors";

/** Age composition as a joy plot: one ridgeline lane per age band (first band
 * on top), peak height = that year's share. Single accent hue — identity is
 * carried by lane position + the band name end-label, not color. Tooltip
 * always reports the REAL percentages from at.pct, never the lane offsets. */
export default function AgeCompositionTrend({ at }: { at: AgeTrend }) {
  const colors = useChartColors();
  if (!at.years.length) return <ChartEmpty height={260}>無分齡資料</ChartEmpty>;
  const lanes = joyRidges(at.pct);
  const height = 60 * at.bands.length + 60;

  const series = lanes.flatMap((lane, bi) => [
    // invisible lane baseline (constant), stacked so the ridge fill sits on it
    { name: `_base${bi}`, type: "line" as const, stack: `joy${bi}`, symbol: "none" as const,
      lineStyle: { opacity: 0 }, data: at.years.map(() => lane.base),
      tooltip: { show: false }, silent: true },
    // the ridge itself (drawn in bi order: lower lanes render later, on top)
    { name: at.bands[bi], type: "line" as const, stack: `joy${bi}`, smooth: 0.4,
      symbol: "none" as const, lineStyle: { color: colors.accent, width: 2 },
      areaStyle: { color: colors.accent, opacity: 0.18 }, data: lane.scaled,
      endLabel: { show: true, formatter: at.bands[bi], color: colors.muted, fontSize: 11 } },
  ]);

  const option: EChartsOption = {
    grid: { left: 16, right: 64, top: 24, bottom: 40 },
    tooltip: {
      trigger: "axis",
      formatter: (params: any) => {
        const idx = Array.isArray(params) && params.length ? params[0].dataIndex : null;
        if (idx == null) return "";
        const rows = at.bands
          .map((b, bi) => ({ b, v: at.pct[bi]?.[idx] }))
          .filter((r) => r.v != null)
          .map((r) => `${r.b}:${(r.v as number).toFixed(1)}%`);
        return `${at.years[idx]}<br/>${rows.join("<br/>")}`;
      },
    },
    xAxis: { type: "category", data: at.years.map(String) },
    yAxis: { type: "value", show: false },
    series,
  };
  return <EChart option={option} height={height} />;
}
