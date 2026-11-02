import { useEffect, useMemo, useState } from "react";
import type { BenchmarkFile } from "../../lib/types";
import { loadBenchmarks } from "../../lib/data-load";
import {
  availableGroups, pickDefaultGroup,
  availableCohorts, pickDefaultCohort, parseFinishTime,
} from "../../lib/benchmark";
import { percentileBeaten, secondsToHMS } from "../../lib/format";
import Skeleton from "../Skeleton";
import DistributionRidge from "../charts/DistributionRidge";
import { useChartColors } from "../../lib/chart-colors";

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

  // open on the most recent, largest race so the page shows an answer right away
  const race = data[rk] ?? races[0]?.[1];
  const activeRk = data[rk] ? rk : races[0]?.[0] ?? "";

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

  const colors = useChartColors();
  const ridgeMarkers = cohort ? [
    { value: cohort.bp[50], label: "中位", color: colors.secondary },
    ...(secs != null && beat != null
      ? [{ value: secs, label: "你", color: colors.accent, labelColor: colors.accent }]
      : []),
  ] : [];

  const onPickRace = (v: string) => { setRk(v); setGroupKey(""); setCohortKey(""); };

  const label = (t: string) => <span className="text-xs text-muted">{t}</span>;

  return (
    <div className="space-y-6">
      {cohort && (
        <section aria-live="polite" className="grid gap-2">
          <p className="font-display text-xl leading-snug text-ink sm:text-2xl" style={{ textWrap: "balance" }}>
            {beat != null ? (
              <>在{race!.rn}「{cohort.label}」的 <span className="num">{cohort.n.toLocaleString("en-US")}</span> 人裡,你贏過
                <span className="num text-accent"> {beat}%</span></>
            ) : (
              <>{race!.rn}「{cohort.label}」中位 <span className="num text-accent">{secondsToHMS(cohort.bp[50])}</span>
                ,輸入你的時間看落點</>
            )}
          </p>
          <p className="num text-sm text-muted">
            最快 {secondsToHMS(cohort.bp[0])} · 中位 {secondsToHMS(cohort.bp[50])} · 最慢 {secondsToHMS(cohort.bp[100])} · {cohort.n.toLocaleString("en-US")} 人
            {cohort.n < 50 && <span className="text-warn"> · 樣本較少,僅供參考</span>}
          </p>
        </section>
      )}

      <div className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <label className="block sm:col-span-2 lg:col-span-1">
          {label("賽事")}
          <select aria-label="選賽事" value={activeRk} onChange={(e) => onPickRace(e.target.value)} className="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-ink">
            {races.map(([k, r]) => {
              const yr = raceYearRange(r);
              const yrLabel = yr.length > 1 && yr[0] !== yr[1] ? `${yr[0]}–${yr[1]}` : (yr[0] ?? "?");
              return <option key={k} value={k}>{r.rn}（{yrLabel}, {raceTotalN(r)} 人）</option>;
            })}
          </select>
        </label>
        {race && hasMultipleGroups && (
          <label className="block">
            {label("距離/組別")}
            <select aria-label="選距離/組別" value={activeGroupKey}
              onChange={(e) => { setGroupKey(e.target.value); setCohortKey(""); }} className="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-ink">
              {groups.map(({ label: l, n }) => <option key={l} value={l}>{l}（{n} 人）</option>)}
            </select>
          </label>
        )}
        {group && (
          <label className="block">
            {label("分組")}
            <select aria-label="選分組" value={activeKey} onChange={(e) => setCohortKey(e.target.value)} className="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-ink">
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
            {label("你的完賽時間")}
            <input value={time} onChange={(e) => setTime(e.target.value)} placeholder="HH:MM:SS 或 MM:SS" inputMode="numeric"
              className="mt-1 w-full rounded-lg border border-border bg-surface px-3 py-2 text-ink outline-none focus:border-accent" />
          </label>
        )}
      </div>
      {cohort && time && beat == null && <p className="text-sm text-warn">時間格式請用 HH:MM:SS 或 MM:SS。</p>}

      {cohort && <DistributionRidge values={cohort.bp} height={220} markers={ridgeMarkers} />}

      <p className="text-xs text-muted">
        以該賽事跨年所有完賽者的完賽時間為基準;分齡用真實年齡組,賽事分組為報名組別。去識別化純聚合,僅供參考。
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
