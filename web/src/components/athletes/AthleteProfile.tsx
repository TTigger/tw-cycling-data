import { useState } from "react";
import { careerSummary, percentileInField, CONF_LABEL } from "../../lib/athletes";
import { secondsToHMS } from "../../lib/format";
import type { AthleteDetail, AthleteIndexEntry } from "../../lib/types";
import AthleteProgression from "./AthleteProgression";
import AthleteRadar from "./AthleteRadar";
import Doppelganger from "./Doppelganger";
import ShareCard from "./ShareCard";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

const CONF_STYLE: Record<string, string> = {
  high: "border-border text-muted",
  med: "border-amber-400/60 bg-amber-50 text-amber-700",
  low: "border-accent/60 bg-accent/10 text-accent",
};

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border bg-surface px-3 py-2">
      <div className="num text-xl text-ink">{value}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );
}

export default function AthleteProfile(
  { d, index, onBack }: { d: AthleteDetail; index: AthleteIndexEntry[]; onBack: () => void },
) {
  const s = careerSummary(d);
  const [showCard, setShowCard] = useState(false);
  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="font-display text-2xl text-ink">{d.nm}</h1>
          <p className="mt-1 text-sm text-muted">
            {s.y0}–{s.y1} · {s.teams.length ? s.teams.join("、") : "無車隊紀錄"}
          </p>
          <span className={`mt-2 inline-block rounded-full border px-2 py-0.5 text-xs ${CONF_STYLE[d.conf]}`}>
            {CONF_LABEL[d.conf]}{d.has_rider && " · TCU ID 串接"}{d.has_uci && " · UCI 串接"}
          </span>
        </div>
        <div className="flex shrink-0 flex-col gap-2">
          <button className="rounded-lg border border-accent bg-accent/10 px-3 py-2 text-sm text-accent hover:bg-accent/20"
            onClick={() => setShowCard(true)}>📇 產生成績卡</button>
          <button className="rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-accent"
            onClick={onBack}>← 換一位</button>
        </div>
      </div>
      {showCard && <ShareCard d={d} onClose={() => setShowCard(false)} />}

      {d.conf !== "high" && (
        <p className="rounded-lg border border-amber-400/50 bg-amber-50 px-3 py-2 text-xs text-amber-700">
          ⚠ 此頁以「遮罩姓名」歸併,
          {d.conf === "low"
            ? "因跨多支車隊或性別不一致,很可能混入多位同名選手,僅供參考。"
            : "可能包含少數同名選手,請對照車隊與年份判讀。"}
        </p>
      )}

      <div className="grid grid-cols-3 gap-3 sm:grid-cols-5">
        <Stat label="出賽場次" value={s.races} />
        <Stat label="涵蓋年數" value={s.years} />
        <Stat label="冠軍" value={s.wins} />
        <Stat label="前三名" value={s.podiums} />
        <Stat label="最佳名次" value={s.bestRank ?? "—"} />
      </div>

      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="font-display text-lg text-ink">進步軌跡</h2>
        <p className="mb-2 text-xs text-muted">每年最佳「同場贏過 % 」(名次/該場人數),跨賽事可比;長條為當年出賽場次。</p>
        <AthleteProgression history={d.history} />
      </section>

      <section className="rounded-xl border border-border bg-surface p-4">
        <h2 className="font-display text-lg text-ink">專長雷達(爬坡 vs 平路)</h2>
        <p className="mb-2 text-xs text-muted">各賽事類型的相對表現,看出選手是爬坡型還是平路型。</p>
        <AthleteRadar traits={d.traits} />
      </section>

      <Doppelganger targetId={d.id} index={index} />

      {d.rivals && d.rivals.length > 0 && (
        <section className="rounded-xl border border-border bg-surface p-4">
          <h2 className="font-display text-lg text-ink">⚔️ 交手戰績(宿敵)</h2>
          <p className="mb-2 text-xs text-muted">最常同場較勁的對手與勝負(同場名次較前者勝)。</p>
          <div className="flex flex-wrap gap-2">
            {d.rivals.map((r) => {
              const lead = r.w > r.l ? "text-emerald-600" : r.w < r.l ? "text-accent" : "text-muted";
              return (
                <a key={r.id} href={`${base}/athletes?id=${r.id}`}
                  className="rounded-lg border border-border bg-bg px-3 py-2 text-sm hover:border-accent">
                  <span className="text-ink">{r.nm}</span>
                  <span className={`ml-2 num ${lead}`}>{r.w}–{r.l}</span>
                  <span className="ml-1 text-xs text-muted">/ {r.meets} 場</span>
                </a>
              );
            })}
          </div>
        </section>
      )}

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
                  <tr key={i} className="border-t border-border/60">
                    <td className="py-1.5 pr-3 num text-muted">{r.y ?? "—"}</td>
                    <td className="py-1.5 pr-3">
                      <a className="text-ink hover:text-accent"
                        href={`${base}/race?rk=${encodeURIComponent(r.rk)}&y=${r.y}`}>{r.rn}</a>
                      {r.label && <span className="ml-1 text-xs text-muted">{r.label}</span>}
                    </td>
                    <td className="py-1.5 pr-3 text-muted">{r.cat ?? "—"}</td>
                    <td className="py-1.5 pr-3 num">{r.rank ?? "—"}{r.field ? <span className="text-muted">/{r.field}</span> : null}</td>
                    <td className="py-1.5 pr-3 num text-muted">{pct == null ? "—" : `${pct}%`}</td>
                    <td className="py-1.5 pr-3 num text-muted">{secondsToHMS(r.t)}</td>
                    <td className="py-1.5 pr-3 text-muted">{r.team ?? "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
