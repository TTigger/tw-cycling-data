import type { AthleteDetail, ClimbVamEntry } from "./types";
import { percentileInField } from "./athletes";
import { specialtyLabel } from "./share-card";

function med(xs: number[]): number | null {
  if (!xs.length) return null;
  const s = [...xs].sort((a, b) => a - b);
  const m = Math.floor(s.length / 2);
  return Math.round(s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2);
}

function yearMedianPct(d: AthleteDetail, year: number): number | null {
  return med(d.history.filter((r) => r.y === year)
    .map((r) => percentileInField(r.rank, r.field))
    .filter((p): p is number => p != null));
}

export interface RecapRace { rn: string; rank: number | null; field: number | null; pct: number | null; }
export interface SeasonRecap {
  year: number;
  races: number;
  medianPct: number | null;          // 該年「贏過全場 %」中位
  deltaVsPrev: number | null;        // vs 去年中位(可能 null,如沒騎去年)
  best: RecapRace | null;            // 最佳一役
  wins: number;
  podiums: number;
  bestVam: { value: number; climb: string } | null;
  busiestMonth: number | null;       // 最常出賽的月份 1-12
  archetype: string | null;
}

/** Spotify-Wrapped-style recap of one season for a rider (data we already have). */
export function seasonRecap(d: AthleteDetail, year: number, vam: ClimbVamEntry[] = []): SeasonRecap {
  const rows = d.history.filter((r) => r.y === year);
  const withPct = rows.map((r) => ({ r, pct: percentileInField(r.rank, r.field) }))
    .filter((x): x is { r: typeof rows[number]; pct: number } => x.pct != null)
    .sort((a, b) => b.pct - a.pct);
  const best = withPct[0];
  const ranks = rows.map((r) => r.rank).filter((x): x is number => x != null);
  const mp = yearMedianPct(d, year);
  const prev = yearMedianPct(d, year - 1);

  const monthCount = new Map<number, number>();
  for (const r of rows) {
    const m = r.d ? Number(r.d.slice(5, 7)) : NaN;
    if (m >= 1 && m <= 12) monthCount.set(m, (monthCount.get(m) || 0) + 1);
  }
  const busiestMonth = [...monthCount.entries()].sort((a, b) => b[1] - a[1])[0]?.[0] ?? null;

  const vy = vam.filter((e) => e.id === d.id && e.y === year);
  const bv = vy.length ? vy.reduce((a, b) => (b.best_vam > a.best_vam ? b : a)) : null;

  return {
    year,
    races: rows.length,
    medianPct: mp,
    deltaVsPrev: mp != null && prev != null ? mp - prev : null,
    best: best ? { rn: best.r.rn, rank: best.r.rank, field: best.r.field, pct: best.pct } : null,
    wins: ranks.filter((r) => r === 1).length,
    podiums: ranks.filter((r) => r <= 3).length,
    bestVam: bv ? { value: Math.round(bv.best_vam), climb: bv.climb } : null,
    busiestMonth,
    archetype: specialtyLabel(d.traits),
  };
}
