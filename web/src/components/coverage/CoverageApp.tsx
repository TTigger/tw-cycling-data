import { useEffect, useMemo, useState } from "react";
import { loadCoverage, loadRaces, loadOverview } from "../../lib/data-load";
import type { Coverage, CoverageGap, RaceIndex } from "../../lib/types";
import type { OverviewData } from "../../lib/overview";
import { sourceInfo } from "../../lib/sources";
import { raceHref } from "../../lib/race-url";
import Skeleton from "../Skeleton";

// Where contributions go. Set this to your preferred channel (GitHub Issues /
// Google Form / community link). Defaults to the project's GitHub.
const CONTRIBUTE_URL = "https://github.com/TTigger/tw-cycling-data";

function Card({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">{title}</h2>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}

const GAP_LABEL: Record<string, string> = {
  NOT_INGESTED: "已辦、待收錄", HELD_UNCHECKED: "已辦、未找到成績", NOT_HELD: "尚未舉辦",
  BLOCKED: "來源讀不到", NO_RANKING: "無排名", FOUND: "已找到、待收錄",
  EXCLUDED: "不收錄", OTHER_LEAGUE: "其他系列", NO_EDITION: "今年未辦",
};

function gapYear(g: CoverageGap): number | null {
  if (g.year) return g.year;
  return g.date ? Number(g.date.slice(0, 4)) : null;
}

interface CoveredRace { rk: string; rn: string; s: string; y0: number; y1: number; rows: number; file: string; }

export default function CoverageApp() {
  const [cov, setCov] = useState<Coverage | null>(null);
  const [races, setRaces] = useState<RaceIndex[]>([]);
  const [ov, setOv] = useState<OverviewData | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadCoverage(), loadRaces(), loadOverview()])
      .then(([c, rs, o]) => { setCov(c); setRaces(rs); setOv(o); })
      .catch((e) => setErr(String(e)));
  }, []);

  // collapse races.json (per race-year) into distinct races with a year span
  const bySeries = useMemo(() => {
    const m = new Map<string, CoveredRace>();
    for (const r of races) {
      const e = m.get(r.rk);
      const y = r.y ?? 0;
      if (!e) m.set(r.rk, { rk: r.rk, rn: r.rn, s: r.s || "其他", y0: y, y1: y, rows: r.rows, file: r.file });
      else { e.y0 = Math.min(e.y0, y); e.y1 = Math.max(e.y1, y); e.rows += r.rows; }
    }
    const groups = new Map<string, CoveredRace[]>();
    for (const c of m.values()) (groups.get(c.s) ?? groups.set(c.s, []).get(c.s)!).push(c);
    return [...groups.entries()]
      .map(([s, list]) => [s, list.sort((a, b) => b.rows - a.rows)] as const)
      .sort((a, b) => b[1].reduce((x, r) => x + r.rows, 0) - a[1].reduce((x, r) => x + r.rows, 0));
  }, [races]);

  // newest year first; entries without a year (mostly no-ranking leisure rides) last
  const sortedGaps = useMemo(() => [...(cov?.gaps ?? [])].sort(
    (a, b) => (gapYear(b) ?? 0) - (gapYear(a) ?? 0) || (b.date ?? "").localeCompare(a.date ?? "")),
  [cov]);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!cov || !ov) return <Skeleton cards={3} />;
  const s = cov.summary;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[["成績筆數", ov.kpi.records.toLocaleString()], ["賽事", ov.kpi.races],
          ["年份", `${ov.kpi.minYear}–${ov.kpi.maxYear}`],
          ["海外賽(另計)", s.overseas.toLocaleString()]].map(([k, v]) => (
          <div key={k} className="rounded-lg border border-border bg-surface px-3 py-2">
            <div className="num text-xl text-ink">{v}</div><div className="text-xs text-muted">{k}</div>
          </div>
        ))}
      </div>

      <Card title="✅ 已收錄的來源" hint="有公開成績系統的競技賽事,大多已收齊">
        <div className="flex flex-wrap gap-2 text-sm">
          {Object.entries(ov.by_source).map(([src, n]) => {
            const info = sourceInfo(src);
            return (
              <span key={src} className="rounded-lg border border-border bg-bg px-3 py-1">
                {info.url
                  ? <a href={info.url} target="_blank" rel="noopener noreferrer" className="text-ink hover:text-accent">{info.name}</a>
                  : <span className="text-ink">{info.name}</span>}
                <span className="num ml-1 text-muted">{n.toLocaleString()}</span>
                <span className="ml-1 text-xs text-muted">{src}</span>
              </span>
            );
          })}
        </div>
      </Card>

      <Card title={`✅ 已收錄賽事(${ov.kpi.races} 場)`} hint="點賽事看排行榜與分析;以系列分組">
        <div className="space-y-3">
          {bySeries.map(([series, list]) => (
            <div key={series}>
              <h3 className="font-display text-sm text-muted">{series}</h3>
              <div className="mt-1 flex flex-wrap gap-2">
                {list.map((r) => (
                  <a key={r.rk} href={raceHref(r.rk, r.y1)}
                    className="rounded-lg border border-border bg-surface px-2.5 py-1 text-xs text-ink hover:border-accent hover:text-accent">
                    {r.rn} <span className="num text-muted">{r.y0 === r.y1 ? r.y0 : `${r.y0}–${r.y1}`}·{r.rows}</span>
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Card>

      <Card title={`⚠️ 已知未收錄(${cov.gaps.length} 場)`}
        hint={`公開行事曆(${s.calendars.length} 個)比對 + 人工維護的已知賽事清單`}>
        <p className="mb-2 text-xs text-muted">
          多數是成績只在主辦自家頁或 FB、沒有公開成績系統的在地/挑戰型賽事;也有已舉辦但成績還沒公布的場次。
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-muted">
              <th className="py-1 pr-3">賽事</th><th className="py-1 pr-3">年份</th>
              <th className="py-1 pr-3">狀態</th><th className="py-1 pr-3">說明</th></tr></thead>
            <tbody>
              {sortedGaps.map((g, i) => (
                <tr key={i} className="border-t border-border/60 align-top">
                  <td className="py-1.5 pr-3 text-ink">
                    {g.url ? <a href={g.url} target="_blank" rel="noopener" className="hover:text-accent">{g.race}</a> : g.race}
                  </td>
                  <td className="num whitespace-nowrap py-1.5 pr-3 text-muted">{gapYear(g) ?? "—"}</td>
                  <td className="whitespace-nowrap py-1.5 pr-3 text-muted">{GAP_LABEL[g.status ?? ""] ?? "待查"}</td>
                  <td className="py-1.5 pr-3 text-xs text-muted">{g.note || (g.guess_source && `推測來源:${g.guess_source}`)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      <Card title="幫忙補資料(投稿)" hint="長尾在地賽要靠社群一起補">
        <p className="text-sm text-ink">看到自己參加的賽事沒被收錄?歡迎提供,讓資料更完整:</p>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">
          <li>賽事<b className="text-ink">名稱 + 日期</b></li>
          <li><b className="text-ink">成績連結</b>(主辦頁/平台網址),或成績<b className="text-ink">圖片/PDF</b>(FB 貼文截圖也行)</li>
        </ul>
        <a href={CONTRIBUTE_URL} target="_blank" rel="noopener"
          className="mt-3 inline-block rounded-lg border border-accent bg-accent/10 px-4 py-2 text-sm text-accent hover:bg-accent/20">
          前往投稿 / 回報 →
        </a>
        <p className="mt-2 text-xs text-muted">成績會去識別化處理(僅顯示遮罩姓名);如為當事人欲下架亦可循此回報。</p>
      </Card>
    </div>
  );
}
