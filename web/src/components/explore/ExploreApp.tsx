import { useEffect, useMemo, useState } from "react";
import { useStore } from "@nanostores/react";
import "../../lib/echarts-theme";
import { loadViz, loadRaces } from "../../lib/data-load";
import { $filters, applyFilters, hydrateFromUrl } from "../../lib/filter-store";
import { facetOptions } from "../../lib/aggregate";
import type { SlimRecord, RaceIndex } from "../../lib/types";
import FilterBar from "./FilterBar";
import FinishTimeHistogram from "../charts/FinishTimeHistogram";
import AgeBoxplot from "../charts/AgeBoxplot";
import CompetitivenessSpread from "../charts/CompetitivenessSpread";
import DistanceSpeedScatter from "../charts/DistanceSpeedScatter";
import Skeleton from "../Skeleton";
import Lead from "../analysis/Lead";
import More from "../analysis/More";
import { summarizeExplore } from "../../lib/explore-summary";
import { secondsToHMS } from "../../lib/format";

export default function ExploreApp() {
  const [viz, setViz] = useState<SlimRecord[] | null>(null);
  const [races, setRaces] = useState<RaceIndex[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const f = useStore($filters);

  useEffect(() => {
    hydrateFromUrl();
    Promise.all([loadViz(), loadRaces()])
      .then(([v, r]) => { setViz(v); setRaces(r); })
      .catch((e) => setErr(String(e)));
  }, []);

  const facets = useMemo(() => (viz ? facetOptions(viz) : null), [viz]);
  const filtered = useMemo(() => (viz ? applyFilters(viz, f) : []), [viz, f]);
  const nameMap = useMemo(() => new Map(races.map((r) => [r.rk, r.rn])), [races]);
  const sum = useMemo(() => summarizeExplore(filtered, !!f.race), [filtered, f.race]);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!viz || !facets) return <Skeleton cards={4} />;

  const fmt = (n: number) => n.toLocaleString("en-US");
  const yrs = sum.yMin == null ? "" : sum.yMin === sum.yMax ? `${sum.yMin}` : `${sum.yMin}–${sum.yMax}`;
  const stats: [string, string][] = [["完賽筆數", fmt(sum.n)]];
  if (sum.races > 1) stats.push(["賽事場數", fmt(sum.races)]);
  if (yrs) stats.push(["年份", yrs]);
  if (sum.womenPct != null) stats.push(["女性占比", `${sum.womenPct}%`]);
  const g = sum.group ?? "";
  if (sum.median != null) stats.push([`${g}中位`, secondsToHMS(sum.median)], [`${g}最快`, secondsToHMS(sum.fastest)]);
  const raceName = f.race ? nameMap.get(f.race) ?? f.race : null;

  return (
    <div className="space-y-8">
      <FilterBar facets={facets} races={races} />
      {sum.n === 0 ? <p className="text-muted">沒有符合條件的成績,試著放寬篩選。</p> : (
        <>
          <Lead stats={stats}>
            {raceName ? <>{raceName}:</> : <>目前條件:</>}
            <span className="num text-accent">{fmt(sum.n)}</span> 筆完賽
            {sum.races > 1 && <>,來自 <span className="num">{fmt(sum.races)}</span> 場賽事</>}
            {sum.median != null && <>,{g}中位 <span className="num">{secondsToHMS(sum.median)}</span></>}。
          </Lead>
          <section>
            <h2 className="font-display text-xl text-ink">完賽時間分布</h2>
            <p className="mb-2 text-xs text-muted">每 10 分鐘一桶{!f.race && " · 混合不同距離的賽事,選單一賽事看得更準"}</p>
            <FinishTimeHistogram rows={filtered} />
          </section>
          <div>
            <More title="分齡組 vs 完賽時間" hint="點組別可篩選 · 僅競技型賽事有分齡"><AgeBoxplot rows={filtered} /></More>
            <More title="賽事競爭強度" hint="中位/冠軍 倍數 · 點賽事可篩選 · 已排除認證型"><CompetitivenessSpread rows={filtered} nameMap={nameMap} /></More>
            <More title="距離 vs 平均速度" hint="距離可解析者約 48%"><DistanceSpeedScatter rows={filtered} /></More>
          </div>
        </>
      )}
    </div>
  );
}
