import { quantile } from "./aggregate";
import type { DetailRow } from "./types";

export function categoriesOf(rows: DetailRow[]): string[] {
  return [...new Set(rows.map((r) => r.cat).filter((c): c is string => !!c))].sort();
}

export interface PodiumEntry { rank: number; name: string | null; team: string | null; t: number | null; }
export function podium(rows: DetailRow[], n = 3): PodiumEntry[] {
  return rows
    .filter((r) => r.rank != null)
    .sort((a, b) => (a.rank as number) - (b.rank as number))
    .slice(0, n)
    .map((r) => ({ rank: r.rank as number, name: r.name, team: r.team, t: r.t }));
}

export interface MainPodium { label: string | null; entries: PodiumEntry[]; }
export function mainPodium(rows: DetailRow[], n = 3): MainPodium {
  const g = new Map<string, DetailRow[]>();
  for (const r of rows) {
    const k = r.cat ?? r.label ?? "";
    const a = g.get(k) || [];
    a.push(r);
    g.set(k, a);
  }
  const minTime = (arr: DetailRow[]) => {
    let m = Infinity;
    for (const r of arr) if (r.t != null && r.t < m) m = r.t;
    return m;
  };
  let bestKey: string | null = null; let best: DetailRow[] = []; let bestMin = Infinity;
  for (const [k, arr] of g) {
    const mt = minTime(arr);
    if (mt < bestMin) { bestMin = mt; best = arr; bestKey = k; }
  }
  const ranked = [...best]
    .filter((r) => r.t != null)
    .sort((a, b) => (a.t as number) - (b.t as number))
    .slice(0, n)
    .map((r, i) => ({ rank: i + 1, name: r.name, team: r.team, t: r.t }));
  return { label: bestKey, entries: ranked };
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
