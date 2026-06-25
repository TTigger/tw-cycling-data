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

export interface ComparableGroup {
  key: string; name: string; cat: string | null; label: string | null;
  rows: DetailRow[]; count: number;
}

const KEY_SEP = "\0";

export function comparableGroups(rows: DetailRow[]): ComparableGroup[] {
  const labelsByCat = new Map<string, Set<string>>();
  for (const r of rows) {
    if (!r.label) continue;
    const c = r.cat ?? "";
    if (!labelsByCat.has(c)) labelsByCat.set(c, new Set());
    labelsByCat.get(c)!.add(r.label);
  }
  const byKey = new Map<string, ComparableGroup>();
  for (const r of rows) {
    const cat = r.cat ?? null;
    const label = r.label ?? null;
    const key = `${cat ?? ""}${KEY_SEP}${label ?? ""}`;
    let g = byKey.get(key);
    if (!g) {
      let name: string;
      if (cat) {
        const multi = (labelsByCat.get(cat)?.size ?? 0) > 1;
        name = multi && label ? `${cat} · ${label}` : cat;
      } else if (label) {
        name = label;
      } else {
        name = "未分組";
      }
      g = { key, name, cat, label, rows: [], count: 0 };
      byKey.set(key, g);
    }
    g.rows.push(r);
    g.count++;
  }
  return [...byKey.values()].sort((a, b) => b.count - a.count || a.name.localeCompare(b.name));
}

export function distinctLabels(rows: DetailRow[]): number {
  return new Set(rows.map((r) => r.label).filter((l): l is string => !!l)).size;
}

export function largestComparableGroup(rows: DetailRow[]): ComparableGroup | null {
  return comparableGroups(rows)[0] ?? null;
}
