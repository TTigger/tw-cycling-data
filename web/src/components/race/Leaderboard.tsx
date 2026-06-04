import { useMemo, useState } from "react";
import { categoriesOf } from "../../lib/racedetail";
import { secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

const PAGE = 50;

export default function Leaderboard({ rows }: { rows: DetailRow[] }) {
  const cats = useMemo(() => categoriesOf(rows), [rows]);
  const [cat, setCat] = useState<string>("");
  const [page, setPage] = useState(0);

  const filtered = useMemo(
    () => (cat ? rows.filter((r) => r.cat === cat) : rows),
    [rows, cat],
  );
  const pages = Math.max(1, Math.ceil(filtered.length / PAGE));
  const p = Math.min(page, pages - 1);
  const slice = filtered.slice(p * PAGE, p * PAGE + PAGE);

  return (
    <div>
      <div className="mb-3 flex items-center gap-3 text-sm">
        <select className="max-w-[14rem] rounded-lg border border-border bg-surface px-3 py-2 text-ink"
          value={cat} onChange={(e) => { setCat(e.target.value); setPage(0); }}>
          <option value="">全部組別</option>
          {cats.map((c) => <option key={c} value={c}>{c}</option>)}
        </select>
        <span className="text-muted">{filtered.length.toLocaleString()} 筆</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-muted">
              <th className="py-2 pr-3">名次</th><th className="pr-3">號碼</th><th className="pr-3">姓名</th>
              <th className="pr-3">組別</th><th className="pr-3">車隊</th><th className="pr-3">完賽</th>
            </tr>
          </thead>
          <tbody>
            {slice.map((r, i) => (
              <tr key={`${r.bib}-${i}`} className="border-b border-border/60">
                <td className="num py-1.5 pr-3">{r.rank ?? "—"}</td>
                <td className="num pr-3 text-muted">{r.bib ?? ""}</td>
                <td className="pr-3 text-ink">{r.name ?? "—"}</td>
                <td className="pr-3 text-muted">{r.cat ?? ""}</td>
                <td className="pr-3 text-muted">{r.team ?? ""}</td>
                <td className="num pr-3">{secondsToHMS(r.t)}</td>
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
