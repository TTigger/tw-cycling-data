import type { AgeTrend, GenderTrend } from "./overview";

export const MIN_KNOWN = 30;   // years with fewer known-gender finishers are not used

export interface ShareChange { from: number; to: number; fromPct: number; toPct: number }
export interface TrendsSummary {
  women: ShareChange | null;
  /** Age band whose share grew most between the same two years, and the one that shrank most. */
  ageUp: { band: string } & ShareChange | null;
  ageDown: { band: string } & ShareChange | null;
  /** Largest age band in the latest complete year. */
  ageTop: { band: string; year: number; pct: number } | null;
}

/** The trends page headline. Compares the first year with enough data against
 * the latest *finished* season (the current year is still in progress, and its
 * mix depends on which sources have published so far). */
export function summarizeTrends(gt: GenderTrend, at: AgeTrend, currentYear: number): TrendsSummary {
  const out: TrendsSummary = { women: null, ageUp: null, ageDown: null, ageTop: null };
  const gi = gt.years.map((y, i) => i).filter((i) => gt.known[i] >= MIN_KNOWN && gt.years[i] < currentYear);
  if (gi.length >= 2) {
    const a = gi[0], b = gi[gi.length - 1];
    out.women = { from: gt.years[a], to: gt.years[b],
      fromPct: Math.round((100 * gt.f[a]) / gt.known[a]), toPct: Math.round((100 * gt.f[b]) / gt.known[b]) };
  }
  const ai = at.years.map((y, i) => i).filter((i) => at.years[i] < currentYear);
  if (ai.length >= 2) {
    const a = ai[0], b = ai[ai.length - 1];
    let up: TrendsSummary["ageUp"] = null, down: TrendsSummary["ageDown"] = null, top: TrendsSummary["ageTop"] = null;
    at.bands.forEach((band, bi) => {
      const p0 = at.pct[bi][a], p1 = at.pct[bi][b];
      const c = { band, from: at.years[a], to: at.years[b], fromPct: p0, toPct: p1 };
      if (!up || p1 - p0 > up.toPct - up.fromPct) up = c;
      if (!down || p1 - p0 < down.toPct - down.fromPct) down = c;
      if (!top || p1 > top.pct) top = { band, year: at.years[b], pct: p1 };
    });
    out.ageUp = up; out.ageDown = down; out.ageTop = top;
  }
  return out;
}
