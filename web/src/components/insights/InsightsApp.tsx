import { useEffect, useState } from "react";
import "../../lib/echarts-theme";
import { loadInsights, loadRaces } from "../../lib/data-load";
import type { Insights, RaceIndex } from "../../lib/types";
import AgeCurve from "./AgeCurve";
import Breakout from "./Breakout";
import RaceRatings from "./RaceRatings";
import ResultConverter from "./ResultConverter";
import GeoHotspots from "./GeoHotspots";
import RecordsWall from "./RecordsWall";
import Skeleton from "../Skeleton";
import Lead from "../analysis/Lead";
import More from "../analysis/More";

export default function InsightsApp() {
  const [ins, setIns] = useState<Insights | null>(null);
  const [races, setRaces] = useState<RaceIndex[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    loadInsights().then(setIns).catch((e) => setErr(String(e)));
    loadRaces().then(setRaces).catch(() => {});
  }, []);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!ins) return <Skeleton cards={4} />;

  const r = ins.records;
  const big = r?.biggest_field[0], starts = r?.most_starts[0], wins = r?.most_wins[0];
  const topRegion = [...ins.geo].sort((a, b) => b.races - a.races)[0];
  const fmt = (n: number) => n.toLocaleString("en-US");
  const stats: [string, string][] = [];
  if (big) stats.push(["單場最多完賽", `${fmt(big.n)} 人`]);
  if (starts) stats.push(["個人最多出賽", `${starts.v} 場`]);
  if (wins) stats.push(["個人最多冠軍", `${wins.v} 次`]);
  if (topRegion) stats.push(["辦最多場的縣市", `${topRegion.region} ${topRegion.races} 場`]);

  return (
    <div className="space-y-8">
      {big && (
        <Lead stats={stats}>
          規模最大的是 {big.y} 年{big.name},<span className="num text-accent">{fmt(big.n)}</span> 人完賽
          {starts && <>;最勤跑的車友出賽 <span className="num">{starts.v}</span> 場</>}。
        </Lead>
      )}

      {r && (
        <section>
          <h2 className="font-display text-xl text-ink">紀錄牆</h2>
          <p className="mb-3 text-xs text-muted">跨全站的極值(已排除高同名風險的身分;點擊前往)</p>
          <RecordsWall records={r} />
        </section>
      )}

      <div>
        <More title="年齡 vs 全場表現" hint="各年齡層在全場的相對名次落點(跨賽事正規化)">
          <AgeCurve points={ins.age_curve} />
        </More>
        <More title="突破之星" hint="年度間相對表現躍升最大的選手">
          <Breakout entries={ins.breakout} />
        </More>
        <More title="賽事地理熱點" hint="各縣市的賽事場數與參賽人次">
          <GeoHotspots regions={ins.geo} />
        </More>
        <More title="賽事星等" hint="規模 × 屆數 × 場域深度的綜合評分">
          <RaceRatings ratings={ins.ratings} />
        </More>
        {races.length > 0 && (
          <More title="成績換算器" hint="你在某場的名次,換算到另一場大約第幾名">
            <ResultConverter races={races} />
          </More>
        )}
      </div>
    </div>
  );
}
