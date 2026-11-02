import { useEffect, useMemo, useState } from "react";
import { loadCoverage, loadRaces } from "../../lib/data-load";
import { buildSeason, seasonYears, shortDate, type SeasonItem, type SeasonStatus } from "../../lib/season";
import type { CoverageGap, RaceIndex } from "../../lib/types";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");
const LIST_N = 8;

const LABEL: Record<SeasonStatus, string> = {
  ok: "已收錄", wait: "成績待收錄", miss: "來源未支援", soon: "即將舉辦",
};
// Square on the month strip / dot in the legend, per status.
const MARK: Record<SeasonStatus, string> = {
  ok: "bg-accent", wait: "bg-summit", miss: "bg-warn", soon: "border border-accent bg-transparent",
};
const PILL: Record<SeasonStatus, string> = {
  ok: "bg-accent/12 text-accent", wait: "bg-summit/15 text-summit",
  miss: "bg-warn/12 text-warn", soon: "border border-border text-muted",
};

function todayISO(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function Row({ it }: { it: SeasonItem }) {
  const name = it.file
    ? <a href={`${base}/race/${encodeURIComponent(it.file)}`} className="text-ink hover:text-accent">{it.name}</a>
    : <span className="text-ink">{it.name}</span>;
  return (
    <li className="grid grid-cols-[3.25rem_1fr_auto] items-baseline gap-3 border-b border-border py-2.5 last:border-b-0">
      <span className="num text-xs text-muted">{shortDate(it.date)}</span>
      <span className="min-w-0">
        <span className="block truncate" title={it.name}>{name}</span>
        {it.series && <span className="text-xs text-muted">{it.series}</span>}
      </span>
      <span className={`whitespace-nowrap rounded-full px-2 py-0.5 text-xs ${PILL[it.status]}`}>
        {it.status === "ok" ? <span className="num">{it.rows?.toLocaleString("en-US")} 人完賽</span> : LABEL[it.status]}
      </span>
    </li>
  );
}

export default function SeasonBoard() {
  const [races, setRaces] = useState<RaceIndex[] | null>(null);
  const [gaps, setGaps] = useState<CoverageGap[]>([]);
  const [year, setYear] = useState<number | null>(null);
  const [today, setToday] = useState("");
  const [showAll, setShowAll] = useState(false);
  const [err, setErr] = useState(false);

  useEffect(() => {
    setToday(todayISO());
    loadRaces().then((r) => { setRaces(r); setYear(seasonYears(r)[0] ?? null); }).catch(() => setErr(true));
    loadCoverage().then((c) => setGaps(c.gaps ?? [])).catch(() => setGaps([]));
  }, []);

  const years = useMemo(() => (races ? seasonYears(races) : []), [races]);
  const season = useMemo(
    () => (races && year && today ? buildSeason(races, gaps, year, today) : null),
    [races, gaps, year, today]);

  if (err) return <p className="text-muted">賽季資料載入失敗,請重新整理頁面。</p>;
  if (!season) {
    return <div className="h-[420px] animate-pulse rounded-2xl bg-surface" aria-label="載入賽季資料" />;
  }

  const upcoming = season.items.filter((i) => i.status === "soon").reverse();   // soonest first
  const past = season.items.filter((i) => i.status !== "soon");
  const list = showAll ? past : past.slice(0, LIST_N);
  const maxInMonth = Math.max(1, ...season.months.map((m) => m.items.length));
  const yi = years.indexOf(season.year);
  const c = season.counts;

  return (
    <section aria-labelledby="season-h">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="eyebrow">賽季看板</p>
          <h2 id="season-h" className="mt-1 font-display text-3xl text-ink sm:text-4xl">{season.year} 賽季</h2>
        </div>
        <div className="flex items-center gap-1 font-mono text-sm" role="group" aria-label="切換年份">
          <button type="button" disabled={yi >= years.length - 1} onClick={() => { setYear(years[yi + 1]); setShowAll(false); }}
            className="rounded-lg border border-border px-2.5 py-1 text-muted hover:border-accent hover:text-accent disabled:opacity-30">
            ‹ {years[yi + 1] ?? ""}
          </button>
          <button type="button" disabled={yi <= 0} onClick={() => { setYear(years[yi - 1]); setShowAll(false); }}
            className="rounded-lg border border-border px-2.5 py-1 text-muted hover:border-accent hover:text-accent disabled:opacity-30">
            {years[yi - 1] ?? ""} ›
          </button>
        </div>
      </div>

      <p className="mt-3 text-muted">
        <span className="num text-ink">{c.ok}</span> 場已收錄
        {c.wait > 0 && <> · <span className="num text-summit">{c.wait}</span> 場已比完、成績待收錄</>}
        {c.miss > 0 && <> · <span className="num text-warn">{c.miss}</span> 場來源未支援</>}
        {c.soon > 0 && <> · <span className="num">{c.soon}</span> 場即將舉辦</>}
      </p>

      {/* month strip: one square per race, stacked from the baseline */}
      <div className="mt-5 rounded-2xl border border-border bg-surface p-4 sm:p-5">
        <div className="grid grid-cols-12 gap-1 sm:gap-2" style={{ minHeight: `${Math.min(maxInMonth, 12) * 10 + 22}px` }}>
          {season.months.map((m) => (
            <div key={m.month} className="flex flex-col justify-end gap-[3px]"
              title={m.items.map((i) => `${shortDate(i.date)} ${i.name}(${LABEL[i.status]})`).join("\n") || undefined}>
              {m.items.slice(0, 12).map((i) => (
                <span key={i.key} className={`block h-[7px] rounded-[2px] ${MARK[i.status]}`} />
              ))}
              {m.items.length > 12 && <span className="text-center text-[10px] text-muted">+{m.items.length - 12}</span>}
              <span className="mt-1 text-center font-mono text-[11px] text-muted">{m.month}</span>
            </div>
          ))}
        </div>
        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
          {(["ok", "wait", "miss", "soon"] as SeasonStatus[]).map((s) => (
            <span key={s} className="inline-flex items-center gap-1.5">
              <span className={`inline-block h-2 w-2 rounded-[2px] ${MARK[s]}`} />{LABEL[s]}
            </span>
          ))}
        </div>
      </div>

      <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_18rem]">
        <div>
          <h3 className="eyebrow">最近的賽事</h3>
          {past.length === 0 ? <p className="mt-3 text-muted">這一年還沒有賽事資料。</p> : (
            <ul className="mt-2">{list.map((it) => <Row key={it.key} it={it} />)}</ul>
          )}
          {past.length > LIST_N && (
            <button type="button" onClick={() => setShowAll((v) => !v)}
              className="mt-3 font-mono text-sm text-accent hover:underline">
              {showAll ? "收合" : `顯示全部 ${past.length} 場`}
            </button>
          )}
        </div>
        <div className="grid content-start gap-6">
          {upcoming.length > 0 && (
            <div>
              <h3 className="eyebrow">接下來</h3>
              <ul className="mt-2">{upcoming.slice(0, 4).map((it) => <Row key={it.key} it={it} />)}</ul>
            </div>
          )}
          {season.undated.length > 0 && (
            <details className="text-sm">
              <summary className="cursor-pointer text-muted">
                另有 <span className="num">{season.undated.length}</span> 場已收錄、但來源沒有提供日期
              </summary>
              <ul className="mt-2">{season.undated.map((it) => <Row key={it.key} it={it} />)}</ul>
            </details>
          )}
          <p className="text-xs leading-relaxed text-muted">
            「成績待收錄」是賽事行事曆上已經辦完、但目前的資料來源還沒有成績的場次,每週自動檢查。
            <a href={`${base}/coverage`} className="text-accent hover:underline">看資料涵蓋 →</a>
          </p>
        </div>
      </div>
    </section>
  );
}
