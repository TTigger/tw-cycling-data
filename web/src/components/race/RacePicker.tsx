import type { RaceIndex } from "../../lib/types";

interface Props { races: RaceIndex[]; onPick: (r: RaceIndex) => void; }

export default function RacePicker({ races, onPick }: Props) {
  const bySeries = new Map<string, RaceIndex[]>();
  for (const r of [...races].sort((a, b) => (b.y ?? 0) - (a.y ?? 0) || b.rows - a.rows)) {
    const s = r.s || "其他";
    const arr = bySeries.get(s) || [];
    arr.push(r);
    bySeries.set(s, arr);
  }
  return (
    <div className="space-y-5">
      <p className="text-muted">選一場賽事查看排行榜與分析:</p>
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
