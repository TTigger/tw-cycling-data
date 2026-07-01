import { useEffect, useMemo, useState } from "react";
import { loadOverview, loadCrossYear, loadRaces } from "../../lib/data-load";
import type { OverviewData, CrossYearMap } from "../../lib/overview";
import type { RaceIndex } from "../../lib/types";
import Skeleton from "../Skeleton";
import GenderShareTrend from "./GenderShareTrend";
import AgeCompositionTrend from "./AgeCompositionTrend";
import FinishTimeBand from "../charts/FinishTimeBand";

export default function TrendsApp() {
  const [ov, setOv] = useState<OverviewData | null>(null);
  const [cy, setCy] = useState<CrossYearMap | null>(null);
  const [races, setRaces] = useState<RaceIndex[] | null>(null);
  const [rk, setRk] = useState("");
  const [groupSel, setGroupSel] = useState("");

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

  if (!ov || !cy || !races) return <Skeleton cards={3} />;
  const activeRk = rk && cy[rk] ? rk : bandRaces[0]?.rk ?? "";

  return (
    <div className="space-y-6">
      <section>
        <h2 className="font-display text-xl">女性參與比例(逐年)</h2>
        <p className="mb-2 text-xs text-muted">僅含已知性別者(約 6 成);樣本太少的年份不畫。</p>
        <GenderShareTrend gt={ov.genderTrend} />
      </section>
      <section>
        <h2 className="font-display text-xl">分齡組成(逐年)</h2>
        <p className="mb-2 text-xs text-muted">僅競技/分組賽有分齡(約 36%);各年為「該年有分齡者」的占比。</p>
        <AgeCompositionTrend at={ov.ageTrend} />
      </section>
      <section>
        <h2 className="font-display text-xl">完賽時間演變(單場跨年)</h2>
        <p className="mb-2 text-xs text-muted">同一賽事跨年比較才公平:中位線 + P25–P75 分布帶 + 冠軍。</p>
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
      </section>
    </div>
  );
}
