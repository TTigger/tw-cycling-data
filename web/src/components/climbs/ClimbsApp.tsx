import { useEffect, useState } from "react";
import "../../lib/echarts-theme";
import { loadRaces, loadRaceDetail, loadClimbProfiles, loadClimbVam, loadCrossYear } from "../../lib/data-load";
import type { CrossYearMap } from "../../lib/overview";
import { summarizeRace } from "../../lib/race-summary";
import RaceSummary from "../race/RaceSummary";
import More from "../analysis/More";
import { climbRaces } from "../../lib/climbs";
import type { RaceIndex, DetailRow, ClimbProfile, ClimbVamEntry } from "../../lib/types";
import VamLeaderboard from "./VamLeaderboard";
import ClimbKingBoard from "./ClimbKingBoard";
import CourseRecords from "./CourseRecords";
import VamMethodology from "./VamMethodology";
import PercentileWidget from "../race/PercentileWidget";
import RaceTimeHistogram from "../race/RaceTimeHistogram";
import Podium from "../race/Podium";
import Skeleton from "../Skeleton";
import Leaderboard from "../race/Leaderboard";

function Card({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">{title}</h2>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}

export default function ClimbsApp() {
  const [climbs, setClimbs] = useState<RaceIndex[]>([]);
  const [sel, setSel] = useState<RaceIndex | null>(null);
  const [detail, setDetail] = useState<DetailRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [profiles, setProfiles] = useState<Record<string, ClimbProfile>>({});
  const [vamRows, setVamRows] = useState<ClimbVamEntry[]>([]);
  const [cy, setCy] = useState<CrossYearMap>({});

  useEffect(() => {
    loadRaces().then((rs) => {
      const cl = climbRaces(rs);
      setClimbs(cl);
      const p = new URLSearchParams(location.search);
      const rk = p.get("rk"), y = p.get("y");
      const m = cl.find((r) => r.rk === rk && String(r.y) === y) ?? cl[0];
      if (m) pick(m, false);
    }).catch((e) => setErr(String(e)));
    loadClimbProfiles().then((ps) => setProfiles(Object.fromEntries(ps.map((p) => [p.race_key, p])))).catch(() => {});
    loadClimbVam().then(setVamRows).catch(() => {});
    loadCrossYear().then(setCy).catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // keep the view in sync with the browser back/forward buttons.
  useEffect(() => {
    if (!climbs.length) return;
    const onPop = () => {
      const p = new URLSearchParams(location.search);
      const rk = p.get("rk"), y = p.get("y");
      const m = climbs.find((r) => r.rk === rk && String(r.y) === y) ?? climbs[0];
      if (m && (!sel || sel.file !== m.file)) pick(m, false);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [climbs, sel]);

  function pick(r: RaceIndex, pushUrl = true) {
    setSel(r); setDetail(null);
    if (pushUrl) history.pushState(null, "", `?rk=${encodeURIComponent(r.rk)}&y=${r.y}`);
    loadRaceDetail(r.file).then(setDetail).catch((e) => setErr(String(e)));
  }

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!climbs.length) return <Skeleton cards={3} />;

  const years = [...new Set(climbs.map((r) => r.y))];
  const base = import.meta.env.BASE_URL.replace(/\/$/, "");

  return (
    <div className="space-y-8">
      <label className="block">
        <span className="text-xs text-muted">選爬坡賽(共 {climbs.length} 場)</span>
        <select aria-label="選爬坡賽" value={sel?.file ?? ""}
          onChange={(e) => { const m = climbs.find((r) => r.file === e.target.value); if (m) pick(m); }}
          className="mt-1 block w-full max-w-xl rounded-lg border border-border bg-surface px-3 py-2 text-ink">
          {years.map((y) => (
            <optgroup key={y} label={String(y)}>
              {climbs.filter((r) => r.y === y).map((r) => (
                <option key={r.file} value={r.file}>{r.y} {r.rn}({r.rows} 人)</option>
              ))}
            </optgroup>
          ))}
        </select>
      </label>

      {sel && (
        <div className="space-y-6">
          <h2 className="font-display text-2xl text-ink">
            {sel.y} {sel.rn}
            <a href={`${base}/race/${encodeURIComponent(sel.file)}`} className="ml-3 align-middle font-mono text-sm text-accent hover:underline">賽事頁 →</a>
          </h2>
          {!detail ? <Skeleton bare cards={2} /> : (
            <>
              <RaceSummary s={summarizeRace(detail, sel.y, sel.completion, cy[sel.rk])} />
              <Card title="你贏過多少%" hint="輸入你的爬坡完賽時間,看落在所有完賽者的前幾%">
                <PercentileWidget rows={detail} />
              </Card>
              <section>
                <h3 className="font-display text-lg text-ink">完賽時間分布</h3>
                <p className="mb-2 text-xs text-muted">每 5 分鐘一桶</p>
                <RaceTimeHistogram rows={detail} />
              </section>
              <div>
                {profiles[sel.rk] && (
                  <More title="爬坡指數 VAM 排行" hint="垂直爬升速度(公尺/小時),跨賽可比">
                    <VamLeaderboard rows={detail} profile={profiles[sel.rk]} />
                  </More>
                )}
                <More title="領獎台與排行榜"><Podium rows={detail} /><div className="mt-4"><Leaderboard rows={detail} /></div></More>
              </div>
            </>
          )}
        </div>
      )}

      <div>
        <p className="eyebrow mb-1">跨賽事</p>
        {vamRows.length > 0 && (
          <More title="跨賽爬坡王" hint="每位選手在所有有路線數據的爬坡賽中的最佳 VAM">
            <ClimbKingBoard entries={vamRows} />
          </More>
        )}
        <More title="場地最速榜" hint="同一條路線歷代最快"><CourseRecords embedded /></More>
        <More title="方法論"><VamMethodology /></More>
      </div>
    </div>
  );
}
