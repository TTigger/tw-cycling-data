import { useEffect, useMemo, useState } from "react";
import type { BenchmarkFile } from "../../lib/types";
import { loadBenchmarks } from "../../lib/data-load";
import { availableCohorts, pickDefaultCohort } from "../../lib/benchmark";
import { percentileBeaten, hmsToSeconds, secondsToHMS } from "../../lib/format";
import Skeleton from "../Skeleton";

function Tool({ data }: { data: BenchmarkFile }) {
  // Race options sorted by latest year then size.
  const races = useMemo(
    () => Object.entries(data).sort(
      (a, b) => (b[1].years.at(-1) ?? 0) - (a[1].years.at(-1) ?? 0)
        || (b[1].cohorts.all?.n ?? 0) - (a[1].cohorts.all?.n ?? 0)),
    [data],
  );
  const [rk, setRk] = useState("");
  const [cohortKey, setCohortKey] = useState("");
  const [time, setTime] = useState("");

  const race = rk ? data[rk] : undefined;
  const cohorts = race ? availableCohorts(race) : [];
  const activeKey = cohortKey && race?.cohorts[cohortKey] ? cohortKey
    : race ? pickDefaultCohort(race) : "";
  const cohort = race?.cohorts[activeKey];
  const secs = hmsToSeconds(time);
  const beat = cohort && secs != null ? percentileBeaten(secs, cohort.bp) : null;

  const onPickRace = (v: string) => { setRk(v); setCohortKey(""); };

  return (
    <div className="space-y-4 text-sm">
      <label className="block">
        <span className="text-muted">① 選賽事</span>
        <select aria-label="選賽事" value={rk} onChange={(e) => onPickRace(e.target.value)}
          className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-ink">
          <option value="">選擇賽事…</option>
          {races.map(([k, r]) => (
            <option key={k} value={k}>{r.rn}（{r.years.at(0)}–{r.years.at(-1)}, {r.cohorts.all?.n ?? 0} 人）</option>
          ))}
        </select>
      </label>

      {race && (
        <label className="block">
          <span className="text-muted">② 選分組</span>
          <select aria-label="選分組" value={activeKey} onChange={(e) => setCohortKey(e.target.value)}
            className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-ink">
            {cohorts.map(({ key, cohort: c }) => (
              <option key={key} value={key}>
                {c.label}（{c.type === "age" ? "分齡" : c.type === "cat" ? "賽事分組" : "全部"}, {c.n} 人）
              </option>
            ))}
          </select>
        </label>
      )}

      {cohort && (
        <label className="block">
          <span className="text-muted">③ 你的完賽時間</span>
          <input value={time} onChange={(e) => setTime(e.target.value)} placeholder="HH:MM:SS"
            className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-ink outline-none focus:border-accent" />
        </label>
      )}

      {cohort && beat != null && (
        <div className="space-y-2 rounded-lg border border-accent/40 bg-accent/10 px-3 py-3 text-ink">
          <div>在「{cohort.label}」({cohort.n} 人),你贏過 <b className="num text-accent">{beat}%</b> 的人。</div>
          <div className="text-xs text-muted">
            最快 {secondsToHMS(cohort.bp[0])}・中位 {secondsToHMS(cohort.bp[50])}・最慢 {secondsToHMS(cohort.bp[100])}
          </div>
          {/* distribution bar: P0..P100 with your marker */}
          <div className="relative h-2 rounded bg-border">
            <div className="absolute top-0 h-2 w-0.5 bg-accent"
              style={{ left: `${Math.min(100, Math.max(0, 100 - beat))}%` }} aria-hidden />
          </div>
          {cohort.n < 50 && <div className="text-xs text-accent">樣本較少({cohort.n} 人),僅供參考。</div>}
        </div>
      )}
      {cohort && time && beat == null && <p className="text-accent">時間格式請用 HH:MM:SS 或 MM:SS。</p>}

      <p className="text-xs text-muted">
        以該賽事跨年所有完賽者的完賽時間為基準;分齡(age)用真實年齡組,賽事分組(cat)為報名組別。去識別化純聚合,僅供參考。
      </p>
    </div>
  );
}

export default function BenchmarkTool() {
  const [data, setData] = useState<BenchmarkFile | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    loadBenchmarks().then(setData).catch((e) => setErr(String(e)));
  }, []);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!data) return <Skeleton cards={2} />;

  return <Tool data={data} />;
}
