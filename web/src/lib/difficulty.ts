import type { AthleteHistoryRow, RaceDifficulty, RaceDifficultyFile } from "./types";

export interface CalibPoint {
  y: number;
  raw: number;         // the rider's raw finish seconds that year
  calibrated: number;  // raw / coeff — normalized to the race's typical year
  coeff: number;       // >1 = that year was hard (slow), <1 = easy (fast)
}

/**
 * A rider's per-year raw vs difficulty-calibrated finish time for one race.
 * Each row is calibrated against its OWN group/distance (`h.label ?? "全部"`) —
 * a year the row's group doesn't cover is strictly skipped (no cross-group
 * fallback). If a rider has several rows in the same race-year, the fastest
 * is kept. Sorted by year.
 */
export function calibratedSeries(
  history: AthleteHistoryRow[], rk: string, diff: RaceDifficulty | undefined,
): CalibPoint[] {
  if (!diff) return [];
  const best = new Map<number, CalibPoint>();
  for (const h of history) {
    if (h.rk !== rk || h.y == null || !h.t) continue;
    const g = h.label || "全部";  // || so an empty-string label maps to 全部, matching the builder
    const yd = diff.groups[g]?.years[String(h.y)];
    if (!yd || !yd.coeff) continue;
    const pt: CalibPoint = {
      y: h.y, raw: h.t, calibrated: Math.round(h.t / yd.coeff), coeff: yd.coeff,
    };
    const cur = best.get(h.y);
    if (!cur || pt.raw < cur.raw) best.set(h.y, pt);
  }
  return [...best.values()].sort((a, b) => a.y - b.y);
}

export type SeverityVerdict = "嚴苛" | "偏難" | "正常" | "偏易";
export interface RaceSeverity {
  year: number;
  group: string;         // the dominant group whose series this severity is read from
  n: number;             // finishers that year
  baselineN: number;     // median finishers across the race's covered years
  finisherDelta: number; // % vs baseline (negative = fewer finishers than usual)
  coeff: number;         // time coeff (>1 = slower than the race's typical year)
  timeDelta: number;     // % vs baseline time (positive = slower)
  verdict: SeverityVerdict;
}

function median(xs: number[]): number {
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
}

/** The race's largest group (by total finishers across covered years) —
 * severity reads this one series so its composition stays stable. */
export function dominantGroup(diff: RaceDifficulty | undefined): string | null {
  if (!diff) return null;
  // ties resolve to the first-encountered group (JSON insertion order)
  let best: string | null = null, bestN = -1;
  for (const [g, grp] of Object.entries(diff.groups)) {
    const n = Object.values(grp.years).reduce((a, y) => a + y.n, 0);
    if (n > bestN) { best = g; bestN = n; }
  }
  return best;
}

/**
 * Attrition/severity proxy for one race-year. We have ONLY finishers (no DNF or
 * registration data), so we compare against the race's own history: far fewer
 * finishers than usual AND slower-than-usual times suggests a brutal edition
 * (weather/conditions). Verdict: 嚴苛 = both fewer & slower; 偏難 = one of them;
 * 偏易 = more finishers & faster; else 正常. Reads the race's dominant group
 * (largest by total n) so the series composition stays stable across years.
 * null if the year isn't covered.
 */
export function raceSeverity(
  diff: RaceDifficulty | undefined, year: number | string | null,
): RaceSeverity | null {
  if (!diff || year == null) return null;
  const gk = dominantGroup(diff);
  const grp = gk ? diff.groups[gk] : undefined;
  const yd = grp?.years[String(year)];
  if (!gk || !grp || !yd) return null;
  const baselineN = median(Object.values(grp.years).map((y) => y.n));
  const finisherDelta = baselineN > 0 ? Math.round((yd.n / baselineN - 1) * 100) : 0;
  const timeDelta = Math.round((yd.coeff - 1) * 100);
  const fewer = finisherDelta <= -20, slower = timeDelta >= 5;
  let verdict: SeverityVerdict = "正常";
  if (fewer && slower) verdict = "嚴苛";
  else if (fewer || slower) verdict = "偏難";
  else if (finisherDelta >= 0 && timeDelta <= -5) verdict = "偏易";
  return {
    year: Number(year), group: gk, n: yd.n, baselineN, finisherDelta,
    coeff: yd.coeff, timeDelta, verdict,
  };
}

/** Severity for every covered year of a race's dominant group, newest first. */
export function raceSeverityAll(diff: RaceDifficulty | undefined): RaceSeverity[] {
  if (!diff) return [];
  const gk = dominantGroup(diff);
  const grp = gk ? diff.groups[gk] : undefined;
  if (!grp) return [];
  return Object.keys(grp.years)
    .map((y) => raceSeverity(diff, y) as RaceSeverity)
    .sort((a, b) => b.year - a.year);
}

export interface CalibratableRace { rk: string; name: string | null; n: number; }

/**
 * Races the rider can see calibrated: ridden (with a time) in >=2 years that the
 * difficulty table covers. Sorted by how many such years (most first).
 */
export function calibratableRaces(
  history: AthleteHistoryRow[], diffFile: RaceDifficultyFile,
): CalibratableRace[] {
  const out: CalibratableRace[] = [];
  for (const rk of new Set(history.map((h) => h.rk))) {
    const diff = diffFile[rk];
    if (!diff) continue;
    const series = calibratedSeries(history, rk, diff);
    if (series.length >= 2) out.push({ rk, name: diff.name, n: series.length });
  }
  return out.sort((a, b) => b.n - a.n || a.rk.localeCompare(b.rk));
}
