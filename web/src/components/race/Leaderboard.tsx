import { useMemo, useState } from "react";
import { comparableGroups, rerankByTime, distinctLabels } from "../../lib/racedetail";
import { secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

const PAGE = 50;
const ALL = "__all__";

export default function Leaderboard({ rows }: { rows: DetailRow[] }) {
  const groups = useMemo(() => comparableGroups(rows), [rows]);
  const showAll = useMemo(() => distinctLabels(rows) <= 1, [rows]);
  const multi = groups.length > 1;
  const options = useMemo(
    () => (multi && showAll ? [{ key: ALL, name: "全部" }, ...groups] : groups),
    [groups, multi, showAll],
  );
  const [sel, setSel] = useState<string>(() => (multi && showAll ? ALL : groups[0]?.key ?? ""));
  const [page, setPage] = useState(0);

  const selectedRows = useMemo(() => {
    if (sel === ALL) return rows;
    return groups.find((g) => g.key === sel)?.rows ?? rows;
  }, [rows, groups, sel]);

  const ranked = useMemo(() => rerankByTime(selectedRows), [selectedRows]);
  const pages = Math.max(1, Math.ceil(ranked.length / PAGE));
  const p = Math.min(page, pages - 1);
  const slice = ranked.slice(p * PAGE, p * PAGE + PAGE);

  return (
    <div>
      <div className="mb-3 flex items-center gap-3 text-sm">
        {multi && (
          <select aria-label="篩選組別" className="max-w-[18rem] rounded-lg border border-border bg-surface px-3 py-2 text-ink"
            value={sel} onChange={(e) => { setSel(e.target.value); setPage(0); }}>
            {options.map((o) => <option key={o.key} value={o.key}>{o.name}</option>)}
          </select>
        )}
        <span className="text-muted">{ranked.length.toLocaleString()} 筆</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted">
              <th className="py-2 pr-3">名次</th><th className="pr-3">號碼</th><th className="pr-3">姓名</th>
              <th className="pr-3">組別</th><th className="pr-3">車隊</th><th className="pr-3">完賽</th>
              <th className="pr-3">原始</th>
            </tr>
          </thead>
          <tbody>
            {slice.map((r, i) => (
              <tr key={`${r.bib}-${i}`} className="border-b border-border/60 transition-colors hover:bg-accent/5">
                <td className="num py-1.5 pr-3">{r.place ?? "—"}</td>
                <td className="num pr-3 text-muted">{r.bib ?? ""}</td>
                <td className="pr-3 text-ink">{r.name ?? "—"}</td>
                <td className="pr-3 text-muted">{r.cat ?? ""}</td>
                <td className="pr-3 text-muted">{r.team ?? ""}</td>
                <td className="num pr-3">{secondsToHMS(r.t)}</td>
                <td className="num pr-3 text-muted">{r.rank ?? ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pages > 1 && (
        <div className="mt-3 flex items-center gap-3 text-sm">
          <button className="rounded border border-border px-2 py-1 text-muted disabled:opacity-40"
            disabled={p <= 0} onClick={() => setPage(p - 1)}>上一頁</button>
          <span className="num text-muted">{p + 1} / {pages}</span>
          <button className="rounded border border-border px-2 py-1 text-muted disabled:opacity-40"
            disabled={p >= pages - 1} onClick={() => setPage(p + 1)}>下一頁</button>
        </div>
      )}
    </div>
  );
}
