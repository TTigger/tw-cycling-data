import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { useChartColors } from "../../lib/chart-colors";
import type { AthleteTrait } from "../../lib/types";

const LABELS: Record<string, string> = { climb: "爬坡", crit: "繞圈", tt: "計時", road: "公路" };
const ORDER = ["climb", "road", "crit", "tt"];

/** Derived specialty label from climb vs flat (road/crit) percentile gap. */
function specialty(traits: Record<string, AthleteTrait>): string | null {
  const climb = traits.climb?.pct;
  const flatVals = [traits.road?.pct, traits.crit?.pct].filter((v): v is number => v != null);
  if (climb == null || !flatVals.length) return null;
  const flat = flatVals.reduce((a, b) => a + b, 0) / flatVals.length;
  const d = climb - flat;
  if (d > 8) return "爬坡型 climber";
  if (d < -8) return "平路型 rouleur";
  return "全能型 all-rounder";
}

export default function AthleteRadar({ traits }: { traits: Record<string, AthleteTrait> }) {
  const colors = useChartColors();
  const types = ORDER.filter((t) => traits[t] && traits[t].n >= 2);
  const label = specialty(traits);

  if (types.length < 2)
    return <p className="text-xs text-muted">跨項目資料不足,無法畫專長雷達(需至少兩種賽事類型各 ≥2 場)。</p>;

  const inner = types.length >= 3 ? (
    (() => {
      const option: EChartsOption = {
        radar: {
          indicator: types.map((t) => ({ name: `${LABELS[t]}\n(${traits[t].n})`, max: 100 })),
          radius: "62%", axisName: { fontSize: 11 },
          splitArea: { areaStyle: { color: ["rgba(0,0,0,0)", "rgba(217,119,87,0.04)"] } },
        },
        tooltip: {},
        series: [{
          type: "radar",
          data: [{ value: types.map((t) => traits[t].pct), name: "贏過全場 %" }],
          itemStyle: { color: colors.accent }, areaStyle: { color: colors.accent, opacity: 0.18 },
        }],
      };
      return <EChart option={option} height={280} />;
    })()
  ) : (
    <div className="space-y-2">
      {types.map((t) => (
        <div key={t} className="flex items-center gap-2 text-sm">
          <span className="w-12 text-muted">{LABELS[t]}</span>
          <div className="h-2 flex-1 rounded bg-border/40">
            <div className="h-2 rounded bg-accent" style={{ width: `${traits[t].pct}%` }} />
          </div>
          <span className="num w-20 text-right text-muted">{traits[t].pct}% ({traits[t].n})</span>
        </div>
      ))}
    </div>
  );

  return (
    <div>
      {label && <p className="mb-2 text-sm text-ink">類型:<span className="text-accent">{label}</span></p>}
      {inner}
      <p className="mt-2 text-xs text-muted">各賽事類型「贏過全場 %」中位數;爬坡明顯高於平路 → 爬坡型,反之 → 平路型。</p>
    </div>
  );
}
