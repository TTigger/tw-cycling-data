import { useState } from "react";
import FinishTimeBand from "../charts/FinishTimeBand";
import ChartEmpty from "../charts/ChartEmpty";
import type { CrossYearPoint } from "../../lib/overview";

/** cy: race_key's group-map (group label -> cross-year points). Shows a group
 * selector when a race mixes distances/events; single-group races auto-select. */
export default function CrossYearTrend({ cy }: { cy: Record<string, CrossYearPoint[]> }) {
  const groups = Object.keys(cy);
  const [sel, setSel] = useState("");
  const active = sel && cy[sel] ? sel : groups[0] ?? "";
  if (!groups.length) return <ChartEmpty height={260}>無跨年資料</ChartEmpty>;
  return (
    <div className="space-y-2">
      {groups.length > 1 && (
        <select aria-label="距離/組別" value={active} onChange={(e) => setSel(e.target.value)}
          className="rounded-lg border border-border bg-surface px-2 py-1 text-xs text-ink">
          {groups.map((g) => <option key={g} value={g}>{g}</option>)}
        </select>
      )}
      <FinishTimeBand cy={cy[active]} />
    </div>
  );
}
