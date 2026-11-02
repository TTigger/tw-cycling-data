import { quantile } from "./aggregate";
import type { CrossYearPoint } from "./overview";
import type { Completion, DetailRow } from "./types";

export interface RaceChange {
  group: string;        // division label the comparison is made on
  prevYear: number;
  deltaSec: number;     // this year's median - previous edition's (negative = faster)
  deltaPct: number;     // relative change, rounded to 0.1
}

export interface RaceSummary {
  finishers: number;
  /** Division the median/fastest are quoted for: the largest one, since
   * divisions can ride different courses (挑戰組 vs 親子組). null = single field. */
  group: string | null;
  groupFinishers: number;
  median: number | null;
  winner: number | null;
  ratePct: number | null;   // completion rate when the source reports DNF/DNS
  change: RaceChange | null;
}

// A year-over-year claim is only made when it is plausibly like-for-like:
// divisions mix categories that can ride different courses (U15 vs elite), and
// a source change can redraw a division. So: the field must be similar in size
// and the move must be in a range real conditions produce.
const MIN_N = 30;
const MAX_FIELD_RATIO = 2;
const MAX_ABS_PCT = 15;

/** Headline numbers for a race-year: finishers, the largest division's median
 * and fastest time,
 * completion rate, and a guarded comparison with the previous edition on this
 * year's largest division. */
export function summarizeRace(rows: DetailRow[], year: number | null,
                              completion: Completion | undefined,
                              crossYear: Record<string, CrossYearPoint[]> | undefined): RaceSummary {
  const byGroup = new Map<string, number[]>();
  let finishers = 0;
  for (const r of rows) {
    if (r.t == null) continue;
    finishers++;
    const g = r.cat ?? r.label ?? "";
    (byGroup.get(g) ?? byGroup.set(g, []).get(g)!).push(r.t);
  }
  let group = "", ts: number[] = [];
  for (const [g, v] of byGroup) if (v.length > ts.length) { group = g; ts = v; }
  ts.sort((a, b) => a - b);
  const out: RaceSummary = {
    finishers,
    group: byGroup.size > 1 ? (group || "未標組別") : null,
    groupFinishers: ts.length,
    median: ts.length ? quantile(ts, 0.5) : null,
    winner: ts.length ? ts[0] : null,
    ratePct: completion && completion.total ? Math.round(completion.rate * 100) : null,
    change: null,
  };
  if (year == null || !crossYear) return out;
  let best: RaceChange | null = null;
  let bestN = 0;
  for (const [group, pts] of Object.entries(crossYear)) {
    const cur = pts.find((p) => p.y === year);
    const prev = pts.filter((p) => p.y < year).sort((a, b) => b.y - a.y)[0];
    if (!cur || !prev || cur.n < MIN_N || prev.n < MIN_N) continue;
    const ratio = cur.n / prev.n;
    if (ratio > MAX_FIELD_RATIO || ratio < 1 / MAX_FIELD_RATIO) continue;
    const pct = ((cur.median - prev.median) / prev.median) * 100;
    if (Math.abs(pct) > MAX_ABS_PCT) continue;
    if (cur.n > bestN) {
      bestN = cur.n;
      best = { group, prevYear: prev.y, deltaSec: cur.median - prev.median, deltaPct: Math.round(pct * 10) / 10 };
    }
  }
  out.change = best;
  return out;
}

/** "11 分 06 秒" style duration for a time difference. */
export function durationText(sec: number): string {
  const s = Math.round(Math.abs(sec));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), ss = s % 60;
  if (h) return `${h} 小時 ${String(m).padStart(2, "0")} 分`;
  if (m) return `${m} 分 ${String(ss).padStart(2, "0")} 秒`;
  return `${ss} 秒`;
}
