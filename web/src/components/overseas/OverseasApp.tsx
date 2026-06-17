import { useEffect, useMemo, useState } from "react";
import { loadOverseasIndex, loadOverseasRace } from "../../lib/data-load";
import type { OverseasRaceMeta, OverseasRow } from "../../lib/types";
import { secondsToHMS } from "../../lib/format";
import Skeleton from "../Skeleton";

const PAGE = 50;

export default function OverseasApp() {
  const [index, setIndex] = useState<OverseasRaceMeta[]>([]);
  const [sel, setSel] = useState<OverseasRaceMeta | null>(null);
  const [rows, setRows] = useState<OverseasRow[] | null>(null);
  const [cat, setCat] = useState("");
  const [page, setPage] = useState(0);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    loadOverseasIndex().then((ix) => {
      setIndex(ix);
      if (ix[0]) pick(ix[0]);
    }).catch((e) => setErr(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function pick(m: OverseasRaceMeta) {
    setSel(m); setRows(null); setCat(""); setPage(0);
    loadOverseasRace(m.file).then(setRows).catch((e) => setErr(String(e)));
  }

  const cats = useMemo(
    () => [...new Set((rows ?? []).map((r) => r.category_raw).filter(Boolean))] as string[],
    [rows],
  );
  const filtered = useMemo(
    () => (rows ?? []).filter((r) => !cat || r.category_raw === cat)
      .sort((a, b) => (a.rank_overall ?? 1e9) - (b.rank_overall ?? 1e9)),
    [rows, cat],
  );
  const pageRows = filtered.slice(page * PAGE, page * PAGE + PAGE);
  const maxPage = Math.max(0, Math.ceil(filtered.length / PAGE) - 1);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!index.length) return <Skeleton cards={2} />;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        {index.map((m) => (
          <button key={m.file} onClick={() => pick(m)}
            className={`rounded-lg border px-3 py-2 text-sm ${sel?.file === m.file ? "border-accent text-accent" : "border-border text-ink hover:border-accent"}`}>
            🌏 {m.race} <span className="num text-muted">({m.region}·{m.n.toLocaleString()})</span>
          </button>
        ))}
      </div>

      {sel && (
        <>
          <div>
            <h1 className="font-display text-2xl text-ink">{sel.race}</h1>
            <p className="text-sm text-muted">{sel.date} · {sel.region} · {sel.source} · {sel.n.toLocaleString()} 位完賽 · 已去識別化</p>
          </div>
          {!rows ? <p className="text-muted">載入成績…</p> : (
            <>
              <div className="flex items-center gap-2 text-sm">
                <span className="text-muted">分組</span>
                <select value={cat} onChange={(e) => { setCat(e.target.value); setPage(0); }}
                  className="max-w-xs rounded-lg border border-border bg-surface px-3 py-2 text-ink">
                  <option value="">全部分組</option>
                  {cats.map((c) => <option key={c} value={c}>{c}</option>)}
                </select>
                <span className="text-xs text-muted">{filtered.length.toLocaleString()} 筆</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-xs text-muted">
                      <th className="py-1 pr-3 num">總名次</th><th className="py-1 pr-3">選手</th>
                      <th className="py-1 pr-3">分組</th><th className="py-1 pr-3">車隊</th>
                      <th className="py-1 pr-3 num">完賽</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pageRows.map((r, i) => (
                      <tr key={i} className="border-t border-border/60">
                        <td className="py-1.5 pr-3 num text-muted">{r.rank_overall ?? "—"}</td>
                        <td className="py-1.5 pr-3 text-ink">{r.name_masked ?? "—"}</td>
                        <td className="py-1.5 pr-3 text-muted">{r.category_raw ?? "—"}</td>
                        <td className="py-1.5 pr-3 text-muted">{r.team ?? "—"}</td>
                        <td className="py-1.5 pr-3 num text-muted">{r.finish_time ?? secondsToHMS(r.finish_seconds)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center gap-3 text-sm">
                <button disabled={page === 0} onClick={() => setPage((p) => p - 1)}
                  className="rounded-lg border border-border px-3 py-1 text-muted disabled:opacity-40">上一頁</button>
                <span className="num text-muted">{page + 1} / {maxPage + 1}</span>
                <button disabled={page >= maxPage} onClick={() => setPage((p) => p + 1)}
                  className="rounded-lg border border-border px-3 py-1 text-muted disabled:opacity-40">下一頁</button>
              </div>
            </>
          )}
        </>
      )}
      <p className="text-xs text-muted">海外賽事為獨立收錄,不計入台灣賽事統計。成績由公開賽事頁(headless 渲染)取得並去識別化。</p>
    </div>
  );
}
