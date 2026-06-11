import { useMemo, useState } from "react";
import type { RaceIndex } from "../../lib/types";

interface Props { races: RaceIndex[]; onPick: (r: RaceIndex) => void; }

export default function RacePicker({ races, onPick }: Props) {
  const [q, setQ] = useState("");
  const query = q.trim();

  const filtered = useMemo(
    () => (query ? races.filter((r) => `${r.y} ${r.rn} ${r.s ?? ""}`.includes(query)) : races),
    [races, query],
  );

  const bySeries = new Map<string, RaceIndex[]>();
  for (const r of [...filtered].sort((a, b) => (b.y ?? 0) - (a.y ?? 0) || b.rows - a.rows)) {
    const s = r.s || "其他";
    const arr = bySeries.get(s) || [];
    arr.push(r);
    bySeries.set(s, arr);
  }

  return (
    <div className="space-y-5">
      <div>
        <p className="text-muted">選一場賽事查看排行榜與分析:</p>
        <input
          value={q} onChange={(e) => setQ(e.target.value)}
          placeholder="搜尋賽事名稱,例如「武嶺」「KOM」「環花東」"
          aria-label="搜尋賽事"
          className="mt-2 w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent"
        />
        {query && (
          <p className="mt-1 text-xs text-muted">{filtered.length} 場符合「{query}」</p>
        )}
      </div>
      {!filtered.length && <p className="text-muted">查無符合的賽事。</p>}
      {[...bySeries.entries()].map(([s, list]) => (
        <div key={s}>
          <h3 className="font-display text-sm text-muted">{s}</h3>
          <div className="mt-2 flex flex-wrap gap-2">
            {list.map((r) => (
              <button key={r.file} onClick={() => onPick(r)}
                className="rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink hover:border-accent hover:text-accent">
                {r.y} {r.rn} <span className="num text-muted">({r.rows})</span>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
