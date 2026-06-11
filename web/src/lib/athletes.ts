import type { AthleteIndexEntry, AthleteHistoryRow, AthleteDetail } from "./types";

/** % of the field this rider beat in one race: (field - rank) / field. null if unknown. */
export function percentileInField(rank: number | null, field: number | null): number | null {
  if (rank == null || !field || field < 1 || rank < 1) return null;
  return Math.round(((field - rank) / field) * 100);
}

/**
 * Client-side athlete search over the (masked) name. Matches a substring of the
 * masked name (e.g. "王" or "王○明"); ranks more-tracked athletes first so the
 * most complete careers surface at the top. Empty query -> the top `limit`.
 */
export function searchAthletes(
  list: AthleteIndexEntry[], query: string, limit = 60,
): AthleteIndexEntry[] {
  const q = query.trim();
  const pool = q ? list.filter((a) => a.nm.includes(q)) : list;
  return [...pool]
    .sort((a, b) => b.n - a.n || b.ny - a.ny || (a.best ?? 9999) - (b.best ?? 9999))
    .slice(0, limit);
}

export interface CareerSummary {
  races: number; years: number; y0: number | null; y1: number | null;
  wins: number; podiums: number; bestRank: number | null; teams: string[];
}

/** Headline career stats from a detail record. */
export function careerSummary(d: AthleteDetail): CareerSummary {
  const h = d.history;
  const ranks = h.map((r) => r.rank).filter((r): r is number => r != null);
  const years = [...new Set(h.map((r) => r.y).filter((y): y is number => y != null))].sort();
  return {
    races: h.length,
    years: years.length,
    y0: years[0] ?? null,
    y1: years[years.length - 1] ?? null,
    wins: ranks.filter((r) => r === 1).length,
    podiums: ranks.filter((r) => r <= 3).length,
    bestRank: ranks.length ? Math.min(...ranks) : null,
    teams: d.teams,
  };
}

export interface ProgressionPoint { y: number; pct: number | null; races: number; bestRank: number | null; }

/**
 * Per-year progression: best in-field percentile (most of the field beaten that
 * year) + races count + best raw rank. Percentile makes years comparable across
 * races of wildly different sizes (elite 30-rider field vs 500-rider citizen ride).
 */
export function progression(history: AthleteHistoryRow[]): ProgressionPoint[] {
  const g = new Map<number, AthleteHistoryRow[]>();
  for (const r of history) {
    if (r.y == null) continue;
    const a = g.get(r.y) || [];
    a.push(r);
    g.set(r.y, a);
  }
  return [...g.entries()]
    .map(([y, rows]) => {
      const pcts = rows.map((r) => percentileInField(r.rank, r.field))
        .filter((p): p is number => p != null);
      const ranks = rows.map((r) => r.rank).filter((r): r is number => r != null);
      return {
        y,
        pct: pcts.length ? Math.max(...pcts) : null,
        races: rows.length,
        bestRank: ranks.length ? Math.min(...ranks) : null,
      };
    })
    .sort((a, b) => a.y - b.y);
}

export const CONF_LABEL: Record<string, string> = {
  high: "身分明確", med: "可能含同名", low: "高同名風險",
};
