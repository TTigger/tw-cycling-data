import { quantile } from "./aggregate";
import type { DetailRow } from "./types";

export interface RankedRow extends DetailRow { place: number | null; }

export function rerankByTime(rows: DetailRow[]): RankedRow[] {
  const withT = rows.filter((r) => r.t != null).sort((a, b) => (a.t as number) - (b.t as number));
  const without = rows.filter((r) => r.t == null);
  return [
    ...withT.map((r, i) => ({ ...r, place: i + 1 })),
    ...without.map((r) => ({ ...r, place: null })),
  ];
}

export function categoriesOf(rows: DetailRow[]): string[] {
  return [...new Set(rows.map((r) => r.cat).filter((c): c is string => !!c))].sort();
}

export interface PodiumEntry { rank: number; name: string | null; team: string | null; t: number | null; }

export function largestCategory(rows: DetailRow[]): string | null {
  const counts = new Map<string, number>();
  for (const r of rows) { if (!r.cat) continue; counts.set(r.cat, (counts.get(r.cat) || 0) + 1); }
  let best: string | null = null; let n = -1;
  for (const [c, k] of counts) if (k > n) { n = k; best = c; }
  return best;
}

export function categoryPodium(rows: DetailRow[], cat: string, n = 3): PodiumEntry[] {
  return rows
    .filter((r) => r.cat === cat && r.t != null)
    .sort((a, b) => (a.t as number) - (b.t as number))
    .slice(0, n)
    .map((r, i) => ({ rank: i + 1, name: r.name, team: r.team, t: r.t }));
}

export interface TeamStat { team: string; top: number; podium: number; }
export function teamStrength(rows: DetailRow[], topN = 10, cutoff = 10): TeamStat[] {
  const g = new Map<string, { top: number; pod: number }>();
  for (const r of rows) {
    if (!r.team || r.rank == null) continue;
    const e = g.get(r.team) || { top: 0, pod: 0 };
    if (r.rank <= cutoff) e.top++;
    if (r.rank <= 3) e.pod++;
    g.set(r.team, e);
  }
  return [...g.entries()]
    .map(([team, e]) => ({ team, top: e.top, podium: e.pod }))
    .filter((t) => t.top > 0)
    .sort((a, b) => b.top - a.top || b.podium - a.podium)
    .slice(0, topN);
}

export interface YearStat { y: number; winner: number; median: number; n: number; }
export function crossYear(rows: { y: number | null; t: number | null }[]): YearStat[] {
  const g = new Map<number, number[]>();
  for (const r of rows) {
    if (r.y == null || r.t == null) continue;
    const a = g.get(r.y) || [];
    a.push(r.t);
    g.set(r.y, a);
  }
  return [...g.entries()]
    .map(([y, ts]) => {
      ts.sort((a, b) => a - b);
      return { y, winner: ts[0], median: quantile(ts, 0.5), n: ts.length };
    })
    .sort((a, b) => a.y - b.y);
}
