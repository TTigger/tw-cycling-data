import { useEffect, useMemo, useState } from "react";
import { loadClimbVam } from "../../lib/data-load";
import { seasonRecap } from "../../lib/season-review";
import { seasonYears } from "../../lib/share-card";
import type { AthleteDetail, ClimbVamEntry } from "../../lib/types";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

function Tile({ kicker, value, sub }: { kicker: string; value: React.ReactNode; sub?: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-bg p-3">
      <div className="text-xs text-muted">{kicker}</div>
      <div className="mt-1 font-display text-2xl text-ink">{value}</div>
      {sub && <div className="mt-0.5 text-xs text-muted">{sub}</div>}
    </div>
  );
}

export default function SeasonReview({ d }: { d: AthleteDetail }) {
  const years = useMemo(() => seasonYears(d), [d]);
  const [year, setYear] = useState(years[0] ?? 0);
  const [vam, setVam] = useState<ClimbVamEntry[]>([]);
  useEffect(() => { loadClimbVam().then(setVam).catch(() => {}); }, []);

  const r = useMemo(() => seasonRecap(d, year, vam), [d, year, vam]);
  if (!years.length) return null;

  const delta = r.deltaVsPrev;
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-lg text-ink">🎬 賽季回顧</h2>
        <div className="flex flex-wrap gap-1">
          {years.map((y) => (
            <button key={y} onClick={() => setYear(y)}
              className={`rounded-full border px-2.5 py-1 text-xs ${
                y === year ? "border-accent bg-accent/10 text-accent" : "border-border text-muted hover:border-accent"
              }`}>{y}</button>
          ))}
        </div>
      </div>

      <p className="mt-2 text-sm text-ink">
        <span className="text-accent">{year}</span> 賽季 — 出賽 <span className="num">{r.races}</span> 場
        {r.archetype && <span className="text-muted"> · {r.archetype}</span>}
      </p>

      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3">
        <Tile kicker="中位贏過全場"
          value={r.medianPct == null ? "—" : `${r.medianPct}%`}
          sub={delta == null ? "首個賽季" : delta >= 0
            ? <span className="text-emerald-600">↑ 較去年 +{delta}</span>
            : <span className="text-accent">↓ 較去年 {delta}</span>} />
        <Tile kicker="冠軍 / 前三" value={<><span>{r.wins}</span><span className="text-muted text-base"> / {r.podiums}</span></>} />
        {r.bestVam && <Tile kicker={`最猛爬坡 · ${r.bestVam.climb}`} value={`VAM ${r.bestVam.value}`} />}
        {r.busiestMonth && <Tile kicker="最活躍月份" value={`${r.busiestMonth} 月`} />}
        {r.best && (
          <div className="col-span-2 rounded-lg border border-accent/40 bg-accent/5 p-3 sm:col-span-3">
            <div className="text-xs text-muted">年度最佳一役</div>
            <a className="mt-1 block font-display text-lg text-ink hover:text-accent"
              href={`${base}/race?rk=${encodeURIComponent(d.history.find((h) => h.rn === r.best!.rn && h.y === year)?.rk ?? "")}&y=${year}`}>
              {r.best.rn}
            </a>
            <div className="mt-0.5 text-sm text-muted">
              名次 <span className="num text-ink">{r.best.rank ?? "—"}{r.best.field ? `/${r.best.field}` : ""}</span>
              {r.best.pct != null && <> · 贏過全場 <span className="num text-accent">{r.best.pct}%</span></>}
            </div>
          </div>
        )}
      </div>
      <p className="mt-2 text-xs text-muted">一年內的高光彙整;百分位為「同場贏過 %」,跨賽事可比,僅供參考。</p>
    </section>
  );
}
