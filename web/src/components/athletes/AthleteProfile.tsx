import { useMemo, useState } from "react";
import { athleteHighlights, careerSummary, percentileInField, searchAthletes, CONF_LABEL } from "../../lib/athletes";
import { raceHref } from "../../lib/race-url";
import { secondsToHMS } from "../../lib/format";
import type { AthleteDetail, AthleteIndexEntry } from "../../lib/types";
import AthleteProgression from "./AthleteProgression";
import CalibratedProgress from "./CalibratedProgress";
import AthleteRadar from "./AthleteRadar";
import Doppelganger from "./Doppelganger";
import SeasonReview from "./SeasonReview";
import ShareCard from "./ShareCard";
import FavButton from "../FavButton";
import Tabs from "../Tabs";
import PercentileTrack from "../PercentileTrack";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

const CONF_STYLE: Record<string, string> = {
  high: "border-border text-muted",
  med: "border-amber-400/60 bg-amber-50 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300",
  low: "border-accent/60 bg-accent/10 text-accent",
};

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="num text-lg text-ink">{value}</dd>
    </div>
  );
}

export default function AthleteProfile(
  { d, index, onBack, onCompare }:
  { d: AthleteDetail; index: AthleteIndexEntry[]; onBack: () => void; onCompare: (id: string) => void },
) {
  const s = careerSummary(d);
  const hl = useMemo(() => athleteHighlights(d), [d]);
  const [showCard, setShowCard] = useState(false);
  const [vsQuery, setVsQuery] = useState<string | null>(null); // null = picker closed
  const vsResults = useMemo(
    () => (vsQuery != null && vsQuery.trim()
      ? searchAthletes(index, vsQuery, 8).filter((x) => x.id !== d.id) : []),
    [index, vsQuery, d.id],
  );
  const [tab, setTab] = useState("overview");
  const tabs = [
    { key: "overview", label: "總覽" },
    { key: "analysis", label: "分析" },
    ...(d.rivals && d.rivals.length ? [{ key: "rivals", label: "對手" }] : []),
    { key: "history", label: "歷年成績" },
  ];
  return (
    <div className="space-y-5">
      <button onClick={onBack} className="text-sm text-muted hover:text-accent">‹ 所有選手</button>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="font-display text-2xl text-ink">{d.nm}</h1>
          <p className="mt-1 text-sm text-muted">
            {s.y0 === s.y1 ? s.y0 : `${s.y0}–${s.y1}`} · {s.teams.length ? s.teams.join("、") : "無車隊紀錄"}
          </p>
          <span className={`mt-2 inline-block rounded-full border px-2 py-0.5 text-xs ${CONF_STYLE[d.conf]}`}>
            {CONF_LABEL[d.conf]}{d.has_rider && " · 以 TCU 編號歸併"}{d.has_uci && " · 以 UCI 編號歸併"}
          </span>
        </div>
        <div className="flex shrink-0 flex-col gap-2">
          <FavButton kind="athlete" item={{ id: d.id, nm: d.nm }} />
          <button className="rounded-lg border border-accent bg-accent/10 px-3 py-2 text-sm text-accent hover:bg-accent/20"
            onClick={() => setShowCard(true)}>產生成績卡</button>
          <button className="rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-accent"
            onClick={() => setVsQuery((q) => (q == null ? "" : null))}>比較選手</button>
        </div>
      </div>
      {showCard && <ShareCard d={d} onClose={() => setShowCard(false)} />}

      {vsQuery != null && (
        <div className="rounded-xl border border-border bg-surface p-3">
          <input autoFocus value={vsQuery} onChange={(e) => setVsQuery(e.target.value)}
            placeholder="搜尋要比較的選手(遮罩姓名,如「王○明」)"
            className="w-full max-w-md rounded-lg border border-border bg-bg px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
          {vsResults.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-2">
              {vsResults.map((x) => (
                <button key={x.id} onClick={() => onCompare(x.id)}
                  className="rounded-lg border border-border bg-bg px-3 py-1.5 text-sm hover:border-accent">
                  <span className="text-ink">{x.nm}</span>
                  <span className="ml-1 text-xs text-muted">{x.n} 場 · {x.y0}–{x.y1}</span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}

      {d.conf !== "high" && (
        <p className="rounded-lg border border-amber-400/50 bg-amber-50 px-3 py-2 text-xs text-amber-700 dark:bg-amber-400/10 dark:text-amber-300">
          ⚠ 此頁以「遮罩姓名」歸併,
          {d.conf === "low"
            ? "因跨多支車隊或性別不一致,很可能混入多位同名選手,僅供參考。"
            : "可能包含少數同名選手,請對照車隊與年份判讀。"}
        </p>
      )}

      {hl.best && (
        <p className="font-display text-xl leading-snug text-ink sm:text-2xl" style={{ textWrap: "balance" }}>
          最好的一場是 {hl.best.y} {hl.best.rn},
          {hl.best.rank === 1
            ? <>拿下<span className="text-accent">第 1 名</span>(<span className="num">{hl.best.field}</span> 人完賽)</>
            : <>贏過 <span className="num text-accent">{hl.best.pct}%</span> 的完賽者</>}
          {hl.latest && (hl.latest.rk !== hl.best.rk || hl.latest.y !== hl.best.y) && (
            <span className="text-muted">;最近一場 {hl.latest.y} {hl.latest.rn} 贏過 <span className="num">{hl.latest.pct}%</span></span>
          )}
        </p>
      )}

      <dl className="grid grid-cols-3 gap-x-6 gap-y-3 sm:flex sm:flex-wrap sm:gap-x-10">
        <Stat label="出賽場次" value={s.races} />
        <Stat label="涵蓋年數" value={s.years} />
        <Stat label="冠軍" value={s.wins} />
        <Stat label="前三名" value={s.podiums} />
        <Stat label="最佳名次" value={s.bestRank ?? "—"} />
      </dl>

      <Tabs tabs={tabs} active={tab} onChange={setTab} />

      {tab === "overview" && (
        <div className="space-y-6">
          {hl.recent.length > 0 && (
            <section aria-labelledby="recent-h">
              <h2 id="recent-h" className="eyebrow">最近成績</h2>
              <ul className="mt-2">
                {hl.recent.map((r, i) => (
                  <li key={i} className="grid grid-cols-[3.5rem_1fr_auto] items-center gap-3 border-b border-border py-2.5 last:border-b-0 sm:grid-cols-[3.5rem_1fr_9rem_auto]">
                    <span className="num text-xs text-muted">{r.d ? r.d.slice(0, 7).replace("-", "/") : r.y ?? "—"}</span>
                    <a href={raceHref(r.rk, r.y)} className="min-w-0 truncate text-ink hover:text-accent" title={r.rn}>{r.rn}</a>
                    <PercentileTrack pct={r.pct} className="hidden w-full sm:inline-block" />
                    <span className="num whitespace-nowrap text-sm">
                      <span className="text-ink">贏過 {r.pct}%</span>
                      <span className="ml-2 text-xs text-muted">{r.rank}/{r.field}</span>
                    </span>
                  </li>
                ))}
              </ul>
              <button type="button" onClick={() => setTab("history")} className="mt-2 font-mono text-sm text-accent hover:underline">
                全部 {d.history.length} 場 →
              </button>
            </section>
          )}
          <SeasonReview d={d} />
          <section className="rounded-xl border border-border bg-surface p-4">
            <h2 className="font-display text-lg text-ink">進步軌跡</h2>
            <p className="mb-2 text-xs text-muted">每年最佳「同場贏過 % 」(名次/該場人數),跨賽事可比;點的大小為當年出賽場次,虛線標生涯最佳年。</p>
            <AthleteProgression history={d.history} />
          </section>
        </div>
      )}

      {tab === "analysis" && (
        <div className="space-y-6">
          <CalibratedProgress history={d.history} />
          <section className="rounded-xl border border-border bg-surface p-4">
            <h2 className="font-display text-lg text-ink">專長雷達(爬坡 vs 平路)</h2>
            <p className="mb-2 text-xs text-muted">各賽事類型的相對表現,看出選手是爬坡型還是平路型。</p>
            <AthleteRadar traits={d.traits} />
          </section>
          <Doppelganger targetId={d.id} index={index} />
        </div>
      )}

      {tab === "rivals" && d.rivals && d.rivals.length > 0 && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="font-display text-lg text-ink">交手戰績(宿敵)</h2>
          <p className="mb-2 text-xs text-muted">最常同場較勁的對手與勝負(同場名次較前者勝)。</p>
          <div className="flex flex-wrap gap-2">
            {d.rivals.map((r) => {
              const lead = r.w > r.l ? "text-emerald-600 dark:text-emerald-400" : r.w < r.l ? "text-accent" : "text-muted";
              const leadLabel = r.w > r.l ? "領先" : r.w < r.l ? "落後" : "平手";
              return (
                <a key={r.id} href={`${base}/athletes?id=${r.id}`}
                  className="rounded-lg border border-border bg-bg px-3 py-2 text-sm hover:border-accent">
                  <span className="text-ink">{r.nm}</span>
                  <span className={`ml-2 num ${lead}`} title={`${leadLabel} ${r.w}勝${r.l}負`}>{r.w}–{r.l}</span>
                  <span className="ml-1 text-xs text-muted">/ {r.meets} 場</span>
                </a>
              );
            })}
          </div>
        </section>
      )}

      {tab === "history" && (
      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="font-display text-lg text-ink">歷年成績</h2>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted">
                <th className="py-1 pr-3">年</th><th className="py-1 pr-3">賽事</th>
                <th className="py-1 pr-3">組別</th><th className="py-1 pr-3 num">名次</th>
                <th className="py-1 pr-3 num">贏過</th><th className="py-1 pr-3 num">完賽</th>
                <th className="py-1 pr-3">車隊</th>
              </tr>
            </thead>
            <tbody>
              {d.history.map((r, i) => {
                const pct = percentileInField(r.rank, r.field);
                return (
                  <tr key={i} className="border-t border-border/60 transition-colors hover:bg-accent/5">
                    <td className="py-1.5 pr-3 num text-muted">{r.y ?? "—"}</td>
                    <td className="py-1.5 pr-3">
                      <a className="text-ink hover:text-accent"
                        href={raceHref(r.rk, r.y)}>{r.rn}</a>
                      {r.label && <span className="ml-1 text-xs text-muted">{r.label}</span>}
                    </td>
                    <td className="py-1.5 pr-3 text-muted">{r.cat ?? "—"}</td>
                    <td className="py-1.5 pr-3 num">{r.rank ?? "—"}{r.field ? <span className="text-muted">/{r.field}</span> : null}</td>
                    <td className="py-1.5 pr-3 num text-muted whitespace-nowrap">
                      {pct == null ? "—" : <><PercentileTrack pct={pct} className="mr-2 w-12" />{pct}%</>}
                    </td>
                    <td className="py-1.5 pr-3 num text-muted">{secondsToHMS(r.t)}</td>
                    <td className="py-1.5 pr-3 text-muted">{r.team ?? "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
      )}
    </div>
  );
}
