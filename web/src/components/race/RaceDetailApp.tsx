import { useEffect, useMemo, useState } from "react";
import "../../lib/echarts-theme";
import { loadRaces, loadCrossYear, loadRaceDetail } from "../../lib/data-load";
import { raceHref } from "../../lib/race-url";
import type { RaceIndex, DetailRow } from "../../lib/types";
import type { CrossYearMap } from "../../lib/overview";
import Tabs from "../Tabs";
import RacePicker from "./RacePicker";
import Leaderboard from "./Leaderboard";
import PercentileWidget from "./PercentileWidget";
import Podium from "./Podium";
import DistributionRidge from "../charts/DistributionRidge";
import { quantile } from "../../lib/aggregate";
import { useChartColors } from "../../lib/chart-colors";
import CrossYearTrend from "./CrossYearTrend";
import TeamStrength from "./TeamStrength";
import RaceDna from "./RaceDna";
import RaceSeverity from "./RaceSeverity";
import Completion from "./Completion";
import Skeleton from "../Skeleton";
import FavButton from "../FavButton";

function Card({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">{title}</h2>
      {hint && <p className="mb-2 text-xs text-muted">{hint}</p>}
      {children}
    </section>
  );
}

const base = import.meta.env.BASE_URL.replace(/\/$/, "");
const RACE_TABS = [{ key: "results", label: "成績" }, { key: "analysis", label: "分析" }, { key: "dna", label: "賽事 DNA" }];

export default function RaceDetailApp({ initRk, initY }: { initRk?: string; initY?: number } = {}) {
  const [races, setRaces] = useState<RaceIndex[]>([]);
  const [crossYear, setCrossYear] = useState<CrossYearMap>({});
  const [sel, setSel] = useState<RaceIndex | null>(null);
  const [detail, setDetail] = useState<DetailRow[] | null>(null);
  const [tab, setTab] = useState("results");
  const [err, setErr] = useState<string | null>(null);
  const colors = useChartColors();

  useEffect(() => {
    Promise.all([loadRaces(), loadCrossYear()]).then(([rs, cy]) => {
      setRaces(rs); setCrossYear(cy);
      const p = new URLSearchParams(location.search);
      // a path-based SSG page (/race/<slug>) passes the race via props; the
      // query-param SPA (/race?rk=&y=) falls back to the URL.
      const rk = initRk ?? p.get("rk"), y = initY != null ? String(initY) : p.get("y");
      if (rk && y) {
        const m = rs.find((r) => r.rk === rk && String(r.y) === y);
        if (m) pick(m, false);
      }
    }).catch((e) => setErr(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // keep the view in sync with the browser back/forward buttons.
  useEffect(() => {
    if (!races.length) return;
    const onPop = () => {
      const p = new URLSearchParams(location.search);
      const rk = initRk ?? p.get("rk"), y = initY != null ? String(initY) : p.get("y");
      if (rk && y) {
        const m = races.find((r) => r.rk === rk && String(r.y) === y);
        if (m) { if (!sel || sel.file !== m.file) pick(m, false); return; }
      }
      setSel(null); setDetail(null);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [races, sel, initRk, initY]);

  function pick(r: RaceIndex, pushUrl = true) {
    setSel(r); setDetail(null); setTab("results");
    if (pushUrl) history.pushState(null, "", `?rk=${encodeURIComponent(r.rk)}&y=${r.y}`);
    loadRaceDetail(r.file).then(setDetail).catch((e) => setErr(String(e)));
  }
  // back to the race list: SSG pages navigate; the SPA just deselects.
  function back() {
    if (initRk) { location.href = `${base}/race`; return; }
    setSel(null); setDetail(null);
    history.pushState(null, "", location.pathname);
  }
  // other years of the same race (for the year-switch pills)
  const siblings = useMemo(
    () => (sel ? races.filter((r) => r.rk === sel.rk).sort((a, b) => (a.y ?? 0) - (b.y ?? 0)) : []),
    [races, sel],
  );

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!races.length) return <Skeleton cards={3} />;

  if (!sel) return <RacePicker races={races} onPick={(r) => pick(r)} />;

  return (
    <div className="space-y-5">
      <button onClick={back} className="text-sm text-muted hover:text-accent">‹ 所有賽事</button>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="font-display text-2xl text-ink">{sel.y} {sel.rn}</h1>
          <p className="text-sm text-muted">{sel.s} · {sel.rows.toLocaleString()} 筆成績</p>
          {siblings.length > 1 && (
            <div className="mt-2 flex flex-wrap gap-1">
              {siblings.map((r) => (r.file === sel.file ? (
                <span key={r.file} className="rounded-full border border-accent bg-accent/10 px-2.5 py-1 text-xs text-accent">{r.y}</span>
              ) : (
                <a key={r.file} href={raceHref(r.rk, r.y)}
                  className="rounded-full border border-border px-2.5 py-1 text-xs text-muted hover:border-accent hover:text-accent">{r.y}</a>
              )))}
            </div>
          )}
        </div>
        {sel.y != null && <FavButton kind="race" item={{ rk: sel.rk, y: sel.y, rn: sel.rn }} />}
      </div>

      {!detail ? <Skeleton bare cards={2} /> : (
        <>
          <Tabs tabs={RACE_TABS} active={tab} onChange={setTab} />
          {tab === "results" && (
            <div className="space-y-4">
              <Card title="領獎台"><Podium rows={detail} /></Card>
              <Card title="你贏過多少%" hint="輸入你的完賽時間"><PercentileWidget rows={detail} /></Card>
              <Card title="排行榜"><Leaderboard rows={detail} /></Card>
            </div>
          )}
          {tab === "analysis" && (
            <div className="space-y-4">
              <div className="grid gap-4 lg:grid-cols-2">
                <Card title="完賽時間分布" hint="每 5 分鐘一桶 · 中位與冠軍標於稜線">
                  {(() => {
                    const ts = detail.map((r) => r.t).filter((t): t is number => t != null);
                    const sorted = [...ts].sort((a, b) => a - b);
                    const markers = sorted.length ? [
                      { value: quantile(sorted, 0.5), label: "中位", color: colors.secondary },
                      { value: sorted[0], label: "冠軍", color: colors.ink },
                    ] : [];
                    return <DistributionRidge values={ts} markers={markers} />;
                  })()}
                </Card>
                {sel.multi_year && <Card title="跨年:變快了嗎" hint="冠軍、中位與 P25–P75 分布"><CrossYearTrend cy={crossYear[sel.rk] ?? {}} /></Card>}
                {sel.has_team && <Card title="車隊戰力榜" hint="前 10 名人次"><TeamStrength rows={detail} /></Card>}
              </div>
              <RaceSeverity rk={sel.rk} year={sel.y} />
              <Completion completion={sel.completion} />
            </div>
          )}
          {tab === "dna" && (
            <Card title="賽事 DNA" hint="六大特徵指紋,可選第二場並排比較">
              <RaceDna rk={sel.rk} year={sel.y} name={sel.rn} />
            </Card>
          )}
        </>
      )}
    </div>
  );
}
