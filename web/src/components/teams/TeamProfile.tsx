import { useState } from "react";
import type { TeamDetail } from "../../lib/types";
import { raceHref } from "../../lib/race-url";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");
const ROSTER_PAGE = 30;

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2">
      <div className="num text-xl text-ink">{value}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );
}

export default function TeamProfile({ d, onBack }: { d: TeamDetail; onBack: () => void }) {
  const [page, setPage] = useState(0);
  const pages = Math.max(1, Math.ceil(d.roster.length / ROSTER_PAGE));
  const p = Math.min(page, pages - 1);
  const slice = d.roster.slice(p * ROSTER_PAGE, p * ROSTER_PAGE + ROSTER_PAGE);
  const peakYear = d.byYear.reduce((a, b) => (b.riders > a.riders ? b : a), d.byYear[0]);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="font-display text-2xl text-ink">{d.name}</h1>
          <p className="mt-1 text-sm text-muted">
            {d.y0}–{d.y1} · {d.riders} 位車手 · 出賽 {d.rows.toLocaleString()} 人次
          </p>
        </div>
        <button className="shrink-0 rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-accent"
          onClick={onBack}>← 換一隊</button>
      </div>

      <div className="grid grid-cols-3 gap-3 sm:grid-cols-5">
        <Stat label="車手" value={d.riders} />
        <Stat label="出賽賽事" value={d.races} />
        <Stat label="冠軍" value={d.wins} />
        <Stat label="前三名" value={d.podiums} />
        <Stat label="最佳名次" value={d.best ?? "—"} />
      </div>

      {peakYear && (
        <p className="text-xs text-muted">
          活躍高峰:{peakYear.y} 年,{peakYear.riders} 位車手出賽 {peakYear.races} 場。
        </p>
      )}

      {d.highlights.length > 0 && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="font-display text-lg text-ink">隊史最佳戰績</h2>
          <p className="mb-2 text-xs text-muted">隊員以此隊名出賽時,「同場贏過 %」最高的成績(跨賽事可比)。</p>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted">
                  <th className="py-1 pr-3">年</th><th className="py-1 pr-3">賽事</th>
                  <th className="py-1 pr-3">車手</th><th className="py-1 pr-3 num">名次</th>
                  <th className="py-1 pr-3 num">贏過</th>
                </tr>
              </thead>
              <tbody>
                {d.highlights.map((h, i) => (
                  <tr key={i} className="border-t border-border/60 transition-colors hover:bg-accent/5">
                    <td className="py-1.5 pr-3 num text-muted">{h.y ?? "—"}</td>
                    <td className="py-1.5 pr-3">
                      {h.rk
                        ? <a className="text-ink hover:text-accent" href={raceHref(h.rk, h.y)}>{h.rn}</a>
                        : <span className="text-ink">{h.rn ?? "—"}</span>}
                    </td>
                    <td className="py-1.5 pr-3">
                      <a className="text-ink hover:text-accent" href={`${base}/athletes?id=${h.id}`}>{h.nm}</a>
                    </td>
                    <td className="py-1.5 pr-3 num">{h.rank ?? "—"}</td>
                    <td className="py-1.5 pr-3 num text-accent">{h.pct}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="font-display text-lg text-ink">車手名單</h2>
        <p className="mb-2 text-xs text-muted">曾以此隊名出賽的車手(依出賽人次排序);姓名已去識別化,以姓名+車隊推斷身分,可能含同名。</p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted">
                <th className="py-1 pr-3">車手</th><th className="py-1 pr-3 num">出賽人次</th>
                <th className="py-1 pr-3 num">最佳名次</th><th className="py-1 pr-3 num">年段</th>
              </tr>
            </thead>
            <tbody>
              {slice.map((r) => (
                <tr key={r.id} className="border-t border-border/60 transition-colors hover:bg-accent/5">
                  <td className="py-1.5 pr-3">
                    {r.link
                      ? <a className="text-ink hover:text-accent" href={`${base}/athletes?id=${r.id}`}>{r.nm}</a>
                      : <span className="text-ink">{r.nm}</span>}
                  </td>
                  <td className="py-1.5 pr-3 num text-muted">{r.n}</td>
                  <td className="py-1.5 pr-3 num">{r.best ?? "—"}</td>
                  <td className="py-1.5 pr-3 num text-muted">{r.y0 === r.y1 ? r.y0 : `${r.y0}–${r.y1}`}</td>
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
      </section>
    </div>
  );
}
