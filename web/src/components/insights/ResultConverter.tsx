import { useMemo, useState } from "react";
import type { RaceIndex } from "../../lib/types";

/** Cross-race result converter: your standing in race A, transferred to race B
 * by in-field percentile. A rough estimate — fields and difficulty differ. */
export default function ResultConverter({ races }: { races: RaceIndex[] }) {
  const opts = useMemo(
    () => [...races].sort((a, b) => (b.y ?? 0) - (a.y ?? 0) || b.rows - a.rows),
    [races],
  );
  const [aFile, setAFile] = useState("");
  const [bFile, setBFile] = useState("");
  const [rank, setRank] = useState("");

  const a = opts.find((r) => r.file === aFile);
  const b = opts.find((r) => r.file === bFile);
  const rk = parseInt(rank, 10);
  const pct = a && rk > 0 && rk <= a.rows ? (a.rows - rk) / a.rows : null;
  const pred = pct != null && b ? Math.max(1, Math.round((1 - pct) * b.rows)) : null;

  const Select = ({ value, onChange, placeholder }: {
    value: string; onChange: (v: string) => void; placeholder: string;
  }) => (
    <select aria-label={placeholder} value={value} onChange={(e) => onChange(e.target.value)}
      className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink">
      <option value="">{placeholder}</option>
      {opts.map((r) => (
        <option key={r.file} value={r.file}>{r.y} {r.rn}（{r.rows} 人）</option>
      ))}
    </select>
  );

  return (
    <div className="space-y-3 text-sm">
      <label className="block">
        <span className="text-muted">① 你參加過的賽事</span>
        <Select value={aFile} onChange={setAFile} placeholder="選擇賽事 A…" />
      </label>
      <label className="block">
        <span className="text-muted">② 你在這場的名次</span>
        <input value={rank} onChange={(e) => setRank(e.target.value)} inputMode="numeric"
          placeholder={a ? `1 – ${a.rows}` : "先選賽事 A"}
          className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-ink outline-none focus:border-accent" />
      </label>
      <label className="block">
        <span className="text-muted">③ 想換算到哪一場</span>
        <Select value={bFile} onChange={setBFile} placeholder="選擇賽事 B…" />
      </label>

      {pred != null && pct != null && b && (
        <div className="rounded-lg border border-accent/40 bg-accent/10 px-3 py-2 text-ink">
          你在 A 贏過 <b className="num text-accent">{Math.round(pct * 100)}%</b> 的人,
          換算到「{b.y} {b.rn}」約為第 <b className="num text-accent">{pred}</b> 名 / {b.rows} 人。
        </div>
      )}
      {a && rk > a.rows && <p className="text-accent">名次不能超過該場完賽人數({a.rows})。</p>}
      <p className="text-xs text-muted">
        以「贏過全場 %」平移估算,假設你的相對實力在不同賽事一致——實際受賽事性質、難度、對手組成影響,僅供參考。
      </p>
    </div>
  );
}
