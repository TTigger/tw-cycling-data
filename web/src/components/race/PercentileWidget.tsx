import { useMemo, useState } from "react";
import { categoriesOf } from "../../lib/racedetail";
import { hmsToSeconds, percentileBeaten, secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

export default function PercentileWidget({ rows }: { rows: DetailRow[] }) {
  const cats = useMemo(() => categoriesOf(rows), [rows]);
  const [cat, setCat] = useState<string>("");
  const [input, setInput] = useState<string>("");

  const times = useMemo(
    () => (cat ? rows.filter((r) => r.cat === cat) : rows)
      .map((r) => r.t).filter((t): t is number => t != null).sort((a, b) => a - b),
    [rows, cat],
  );
  const mine = hmsToSeconds(input);
  const pct = mine != null && times.length ? percentileBeaten(mine, times) : null;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-end gap-3 text-sm">
        <label className="flex flex-col gap-1">
          <span className="text-muted">組別</span>
          <select className="max-w-[14rem] rounded-lg border border-border bg-surface px-3 py-2 text-ink"
            value={cat} onChange={(e) => setCat(e.target.value)}>
            <option value="">全部</option>
            {cats.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </label>
        <label className="flex flex-col gap-1">
          <span className="text-muted">你的完賽時間 (時:分:秒)</span>
          <input className="rounded-lg border border-border bg-surface px-3 py-2 text-ink num"
            placeholder="2:30:00" value={input} onChange={(e) => setInput(e.target.value)} />
        </label>
      </div>
      {input && mine == null && <p className="text-sm text-accent">請輸入 時:分:秒(例 2:30:00)</p>}
      {pct != null && (
        <p className="text-lg text-ink">
          你贏過 <span className="num text-2xl text-accent">{pct}%</span> 的完賽者
          <span className="text-sm text-muted">(中位 {secondsToHMS(times[Math.floor(times.length / 2)])} · {times.length} 人)</span>
        </p>
      )}
    </div>
  );
}
