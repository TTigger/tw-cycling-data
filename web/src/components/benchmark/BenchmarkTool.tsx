import { useEffect, useMemo, useState } from "react";
import type { BenchmarkFile } from "../../lib/types";
import { loadBenchmarks } from "../../lib/data-load";
import {
  availableGroups, pickDefaultGroup,
  availableCohorts, pickDefaultCohort, parseFinishTime,
} from "../../lib/benchmark";
import { percentileBeaten, secondsToHMS } from "../../lib/format";
import Skeleton from "../Skeleton";

/** Latest year across all groups in a race. */
function raceMaxYear(r: BenchmarkFile[string]): number {
  return Math.max(...Object.values(r.groups).flatMap((g) => g.years), 0);
}

/** Total finisher count across all groups (sum of each group's `all` cohort). */
function raceTotalN(r: BenchmarkFile[string]): number {
  return Object.values(r.groups).reduce((acc, g) => acc + (g.cohorts.all?.n ?? 0), 0);
}

/** Earliest–latest years across all groups (for display). */
function raceYearRange(r: BenchmarkFile[string]): number[] {
  const all = Object.values(r.groups).flatMap((g) => g.years);
  if (!all.length) return [];
  return [Math.min(...all), Math.max(...all)];
}

function Tool({ data }: { data: BenchmarkFile }) {
  // Race options sorted by latest year then total size.
  const races = useMemo(
    () => Object.entries(data).sort(
      (a, b) => raceMaxYear(b[1]) - raceMaxYear(a[1])
        || raceTotalN(b[1]) - raceTotalN(a[1])),
    [data],
  );

  const [rk, setRk] = useState("");
  const [groupKey, setGroupKey] = useState("");
  const [cohortKey, setCohortKey] = useState("");
  const [time, setTime] = useState("");

  const race = rk ? data[rk] : undefined;

  // Derive the active group key (validated; falls back to default).
  const activeGroupKey = groupKey && race?.groups[groupKey]
    ? groupKey
    : race ? pickDefaultGroup(race) : "";
  const group = race?.groups[activeGroupKey];

  const groups = race ? availableGroups(race) : [];
  const hasMultipleGroups = groups.length > 1;

  const cohorts = group ? availableCohorts(group) : [];
  const activeKey = cohortKey && group?.cohorts[cohortKey] ? cohortKey
    : group ? pickDefaultCohort(group) : "";
  const cohort = group?.cohorts[activeKey];

  const secs = parseFinishTime(time);
  const beat = cohort && secs != null ? percentileBeaten(secs, cohort.bp) : null;

  const onPickRace = (v: string) => { setRk(v); setGroupKey(""); setCohortKey(""); };

  // Step numbers shift when the group dropdown is visible.
  const stepCohort = hasMultipleGroups ? "③" : "②";
  const stepTime   = hasMultipleGroups ? "④" : "③";

  return (
    <div className="space-y-4 text-sm">
      <label className="block">
        <span className="text-muted">① 選賽事</span>
        <select aria-label="選賽事" value={rk} onChange={(e) => onPickRace(e.target.value)}
          className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-ink">
          <option value="">選擇賽事…</option>
          {races.map(([k, r]) => {
            const yr = raceYearRange(r);
            const yrLabel = yr.length > 1 && yr[0] !== yr[1]
              ? `${yr[0]}–${yr[1]}` : (yr[0] ?? "?");
            return (
              <option key={k} value={k}>{r.rn}（{yrLabel}, {raceTotalN(r)} 人）</option>
            );
          })}
        </select>
      </label>

      {race && hasMultipleGroups && (
        <label className="block">
          <span className="text-muted">② 選距離/組別</span>
          <select aria-label="選距離/組別" value={activeGroupKey}
            onChange={(e) => { setGroupKey(e.target.value); setCohortKey(""); }}
            className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-ink">
            {groups.map(({ label, n }) => (
              <option key={label} value={label}>{label}（{n} 人）</option>
            ))}
          </select>
        </label>
      )}

      {group && (
        <label className="block">
          <span className="text-muted">{stepCohort} 選分組</span>
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
          <span className="text-muted">{stepTime} 你的完賽時間</span>
          <input value={time} onChange={(e) => setTime(e.target.value)} placeholder="HH:MM:SS 或 MM:SS"
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
