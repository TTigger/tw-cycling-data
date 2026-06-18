import { useEffect, useState } from "react";
import "../../lib/echarts-theme";
import { loadRaces, loadRaceDetail, loadClimbProfiles, loadClimbVam } from "../../lib/data-load";
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

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {climbs.map((r) => (
          <button key={r.file} onClick={() => pick(r)}
            className={`rounded-lg border px-3 py-2 text-sm ${
              sel && sel.file === r.file ? "border-accent text-accent" : "border-border text-ink hover:border-accent"
            }`}>
            {r.y} {r.rn} <span className="num text-muted">({r.rows})</span>
          </button>
        ))}
      </div>

      {sel && (
        <>
          <h1 className="font-display text-2xl text-ink">{sel.y} {sel.rn}</h1>
          {!detail ? <p className="text-muted">載入成績…</p> : (
            <div className="space-y-6">
              {sel && profiles[sel.rk] && (
                <Card title="爬坡指數 VAM 排行" hint="垂直爬升速度(公尺/小時),跨賽可比">
                  <VamLeaderboard rows={detail} profile={profiles[sel.rk]} />
                </Card>
              )}
              <Card title="你贏過多少%" hint="輸入你的爬坡完賽時間,看落在所有完賽者的前幾%">
                <PercentileWidget rows={detail} />
              </Card>
              <div className="grid gap-4 lg:grid-cols-2">
                <Card title="全民完賽時間分布" hint="每 5 分鐘一桶"><RaceTimeHistogram rows={detail} /></Card>
                <Card title="領獎台"><Podium rows={detail} /></Card>
              </div>
              <Card title="排行榜"><Leaderboard rows={detail} /></Card>
            </div>
          )}
        </>
      )}
      {vamRows.length > 0 && (
        <Card title="🏔 跨賽爬坡王" hint="每位選手在所有有路線數據的爬坡賽中的最佳 VAM">
          <ClimbKingBoard entries={vamRows} />
        </Card>
      )}
      <CourseRecords />
      <Card title="方法論"><VamMethodology /></Card>
    </div>
  );
}
