import { useEffect, useMemo, useState } from "react";
import "../../lib/echarts-theme";
import { loadRaces, loadViz, loadRaceDetail } from "../../lib/data-load";
import type { RaceIndex, DetailRow, SlimRecord } from "../../lib/types";
import RacePicker from "./RacePicker";
import Leaderboard from "./Leaderboard";
import PercentileWidget from "./PercentileWidget";
import Podium from "./Podium";
import RaceTimeHistogram from "./RaceTimeHistogram";
import CrossYearTrend from "./CrossYearTrend";
import TeamStrength from "./TeamStrength";
import RaceDna from "./RaceDna";
import RaceSeverity from "./RaceSeverity";
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

export default function RaceDetailApp({ initRk, initY }: { initRk?: string; initY?: number } = {}) {
  const [races, setRaces] = useState<RaceIndex[]>([]);
  const [viz, setViz] = useState<SlimRecord[]>([]);
  const [sel, setSel] = useState<RaceIndex | null>(null);
  const [detail, setDetail] = useState<DetailRow[] | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([loadRaces(), loadViz()]).then(([rs, v]) => {
      setRaces(rs); setViz(v);
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

  function pick(r: RaceIndex, pushUrl = true) {
    setSel(r); setDetail(null);
    if (pushUrl) history.pushState(null, "", `?rk=${encodeURIComponent(r.rk)}&y=${r.y}`);
    loadRaceDetail(r.file).then(setDetail).catch((e) => setErr(String(e)));
  }

  const crossRows = useMemo(
    () => (sel ? viz.filter((v) => v.rk === sel.rk).map((v) => ({ y: v.y, t: v.t })) : []),
    [viz, sel],
  );

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!races.length) return <Skeleton cards={3} />;

  if (!sel) return <RacePicker races={races} onPick={(r) => pick(r)} />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl text-ink">{sel.y} {sel.rn}</h1>
          <p className="text-sm text-muted">{sel.s} · {sel.rows.toLocaleString()} 筆成績</p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          {sel.y != null && <FavButton kind="race" item={{ rk: sel.rk, y: sel.y, rn: sel.rn }} />}
          <button className="rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-accent"
            onClick={() => { setSel(null); history.pushState(null, "", location.pathname); }}>← 換一場</button>
        </div>
      </div>

      {!detail ? <p className="text-muted">載入排行榜…</p> : (
        <>
          <Card title="領獎台"><Podium rows={detail} /></Card>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card title="你贏過多少%" hint="輸入你的完賽時間"><PercentileWidget rows={detail} /></Card>
            <Card title="完賽時間分布" hint="每 5 分鐘一桶"><RaceTimeHistogram rows={detail} /></Card>
            {sel.multi_year && <Card title="跨年:變快了嗎" hint="冠軍與中位完賽時間"><CrossYearTrend rows={crossRows} /></Card>}
            {sel.has_team && <Card title="車隊戰力榜" hint="前 10 名人次"><TeamStrength rows={detail} /></Card>}
          </div>
          <RaceSeverity rk={sel.rk} year={sel.y} />
          <Card title="🧬 賽事 DNA" hint="六大特徵指紋,可選第二場並排比較">
            <RaceDna rk={sel.rk} year={sel.y} name={sel.rn} />
          </Card>
          <Card title="排行榜"><Leaderboard rows={detail} /></Card>
        </>
      )}
    </div>
  );
}
