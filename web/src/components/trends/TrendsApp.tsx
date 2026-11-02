import { useEffect, useMemo, useState } from "react";
import { loadOverview, loadCrossYear, loadRaces } from "../../lib/data-load";
import type { OverviewData, CrossYearMap } from "../../lib/overview";
import type { RaceIndex } from "../../lib/types";
import Skeleton from "../Skeleton";
import GenderShareTrend from "./GenderShareTrend";
import AgeCompositionTrend from "./AgeCompositionTrend";
import FinishTimeBand from "../charts/FinishTimeBand";
import Lead from "../analysis/Lead";
import More from "../analysis/More";
import { summarizeTrends } from "../../lib/trends-summary";

export default function TrendsApp() {
  const [ov, setOv] = useState<OverviewData | null>(null);
  const [cy, setCy] = useState<CrossYearMap | null>(null);
  const [races, setRaces] = useState<RaceIndex[] | null>(null);
  const [rk, setRk] = useState("");
  const [groupSel, setGroupSel] = useState("");
  const [year] = useState(() => new Date().getFullYear());

  useEffect(() => {
    Promise.all([loadOverview(), loadCrossYear(), loadRaces()])
      .then(([o, c, r]) => { setOv(o); setCy(c); setRaces(r); })
      .catch(() => { setOv(null); });
  }, []);

  // multi-year races that have band data, labelled from the races index
  const bandRaces = useMemo(() => {
    if (!cy || !races) return [];
    const name = new Map(races.map((r) => [r.rk, r.rn] as const));
    return Object.keys(cy)
      .filter((k) => Object.keys(cy[k]).length > 0)
      .map((k) => {
        const n = Math.max(...Object.values(cy[k]).map((pts) => pts.length), 0);
        return { rk: k, rn: name.get(k) ?? k, n };
      })
      .sort((a, b) => b.n - a.n);
  }, [cy, races]);

  const sum = useMemo(() => (ov ? summarizeTrends(ov.genderTrend, ov.ageTrend, year) : null), [ov, year]);

  if (!ov || !cy || !races || !sum) return <Skeleton cards={3} bare />;
  const activeRk = rk && cy[rk] ? rk : bandRaces[0]?.rk ?? "";

  const { women: w, ageUp: up, ageDown: down, ageTop: top } = sum;
  const stats: [string, string][] = [];
  if (w) stats.push([`女性占比 ${w.to}`, `${w.toPct}%`], [`女性占比 ${w.from}`, `${w.fromPct}%`]);
  if (top) stats.push([`最大年齡層 ${top.year}`, `${top.band} 歲(${top.pct}%)`]);
  if (down) stats.push([`${down.band} 歲占比`, `${down.fromPct}% → ${down.toPct}%`]);

  return (
    <div className="space-y-8">
      {w && (
        <Lead stats={stats} note={<>早年資料多為競技賽,2022 年起收錄大量休閒型賽事,部分變化來自收錄範圍改變。只算已知性別/分齡的完賽者;{year} 賽季還在進行,不列入比較。</>}>
          女性完賽者從 {w.from} 年的 <span className="num">{w.fromPct}%</span> 升到 {w.to} 年的
          <span className="num text-accent"> {w.toPct}%</span>
          {up && down && up.band !== down.band && <>;年齡層也往上移,{down.band} 歲的占比少了 {down.fromPct - down.toPct} 個百分點,{up.band} 歲多了 {up.toPct - up.fromPct} 個</>}
          。
        </Lead>
      )}

      <section>
        <h2 className="font-display text-xl">女性參與比例(逐年)</h2>
        <p className="mb-2 text-xs text-muted">僅含已知性別者(約 6 成);樣本太少的年份不畫。</p>
        <GenderShareTrend gt={ov.genderTrend} />
      </section>

      <div>
      <More title="分齡組成(逐年)" hint="僅競技/分組賽有分齡,約 36% 的完賽者">
        <AgeCompositionTrend at={ov.ageTrend} />
      </More>
      <More title="單場賽事跨年完賽時間" hint="同一賽事跨年比較才公平:中位線、P25–P75 分布帶、冠軍">
        <select aria-label="選賽事" value={activeRk} onChange={(e) => { setRk(e.target.value); setGroupSel(""); }}
          className="mb-2 w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink">
          {bandRaces.map((r) => <option key={r.rk} value={r.rk}>{r.rn}（{r.n} 年）</option>)}
        </select>
        {activeRk && (() => {
          const groupMap = cy[activeRk] ?? {};
          const groups = Object.keys(groupMap);
          const activeGroup = groupSel && groupMap[groupSel] ? groupSel : groups[0] ?? "";
          return (
            <>
              {groups.length > 1 && (
                <select aria-label="距離/組別" value={activeGroup} onChange={(e) => setGroupSel(e.target.value)}
                  className="mb-2 ml-2 rounded-lg border border-border bg-surface px-2 py-1 text-sm text-ink">
                  {groups.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
              )}
              {activeGroup && <FinishTimeBand cy={groupMap[activeGroup]} />}
            </>
          );
        })()}
      </More>
      </div>
    </div>
  );
}
