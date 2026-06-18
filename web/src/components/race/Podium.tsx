import { useMemo, useState } from "react";
import { categoriesOf, largestCategory, categoryPodium } from "../../lib/racedetail";
import { secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

const MEDAL = ["#D9A441", "#9FA6AD", "#B07A52"];

export default function Podium({ rows }: { rows: DetailRow[] }) {
  const cats = useMemo(() => categoriesOf(rows), [rows]);
  const [cat, setCat] = useState<string>(() => largestCategory(rows) ?? cats[0] ?? "");
  const entries = useMemo(() => (cat ? categoryPodium(rows, cat, 3) : []), [rows, cat]);
  if (!cats.length) return <p className="text-muted">無組別名次資料</p>;
  return (
    <div>
      <select aria-label="選擇組別" className="mb-3 max-w-[14rem] rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink"
        value={cat} onChange={(e) => setCat(e.target.value)}>
        {cats.map((c) => <option key={c} value={c}>{c}</option>)}
      </select>
      <div className="flex flex-wrap gap-3">
        {entries.map((p, i) => (
          <div key={i} className="min-w-[140px] flex-1 rounded-xl border border-border bg-surface p-3">
            <div className="num text-lg" style={{ color: MEDAL[i] }}>#{p.rank}</div>
            <div className="text-ink">{p.name ?? "—"}</div>
            <div className="text-xs text-muted">{p.team ?? ""}</div>
            <div className="num text-sm text-muted">{secondsToHMS(p.t)}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
