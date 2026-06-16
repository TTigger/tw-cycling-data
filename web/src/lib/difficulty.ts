import type { AthleteHistoryRow, RaceDifficulty, RaceDifficultyFile } from "./types";

export interface CalibPoint {
  y: number;
  raw: number;         // the rider's raw finish seconds that year
  calibrated: number;  // raw / coeff — normalized to the race's typical year
  coeff: number;       // >1 = that year was hard (slow), <1 = easy (fast)
}

/**
 * A rider's per-year raw vs difficulty-calibrated finish time for one race.
 * Only years present in both the rider's history (with a time) and the race's
 * difficulty table. If a rider has several rows in the same race-year, the
 * fastest is kept. Sorted by year.
 */
export function calibratedSeries(
  history: AthleteHistoryRow[], rk: string, diff: RaceDifficulty | undefined,
): CalibPoint[] {
  if (!diff) return [];
  const best = new Map<number, CalibPoint>();
  for (const h of history) {
    if (h.rk !== rk || h.y == null || !h.t) continue;
    const yd = diff.years[String(h.y)];
    if (!yd || !yd.coeff) continue;
    const pt: CalibPoint = {
      y: h.y, raw: h.t, calibrated: Math.round(h.t / yd.coeff), coeff: yd.coeff,
    };
    const cur = best.get(h.y);
    if (!cur || pt.raw < cur.raw) best.set(h.y, pt);
  }
  return [...best.values()].sort((a, b) => a.y - b.y);
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
