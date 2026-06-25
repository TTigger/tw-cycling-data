import { useMemo, useState } from "react";
import { comparableGroups, rerankByTime } from "../../lib/racedetail";
import { secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

const MEDAL = ["#D9A441", "#9FA6AD", "#B07A52"];

export default function Podium({ rows }: { rows: DetailRow[] }) {
  const groups = useMemo(() => comparableGroups(rows), [rows]);
  const [sel, setSel] = useState<string>(() => groups[0]?.key ?? "");
  const entries = useMemo(() => {
    const g = groups.find((x) => x.key === sel) ?? groups[0];
    return g ? rerankByTime(g.rows).filter((r) => r.t != null).slice(0, 3) : [];
  }, [groups, sel]);
  if (!groups.length) return <p className="text-muted">無組別名次資料</p>;
  return (
    <div>
      {groups.length > 1 && (
        <select aria-label="選擇組別" className="mb-3 max-w-[18rem] rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink"
          value={sel} onChange={(e) => setSel(e.target.value)}>
          {groups.map((g) => <option key={g.key} value={g.key}>{g.name}</option>)}
        </select>
      )}
      <div className="flex flex-wrap gap-3">
        {entries.map((p, i) => (
          <div key={i} className="min-w-[140px] flex-1 rounded-xl border border-border bg-surface p-3">
            <div className="num text-lg" style={{ color: MEDAL[i] }}>#{p.place}</div>
            <div className="text-ink">{p.name ?? "—"}</div>
            <div className="text-xs text-muted">{p.team ?? ""}</div>
            <div className="num text-sm text-muted">{secondsToHMS(p.t)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
