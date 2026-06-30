import type { SlimRecord } from "./types";

/** Shape of the precomputed homepage payload (scrapers/build_viz.build_overview)
 * — lets the landing page skip the 24MB viz.json. The functions below still
 * document & test the same aggregations (used by overview.test.ts). */
export interface CrossYearPoint { y: number; winner: number; median: number; p25: number; p75: number; n: number; }
export type CrossYearMap = Record<string, CrossYearPoint[]>;

export interface GenderTrend { years: number[]; f: number[]; known: number[]; }
export interface AgeTrend { years: number[]; bands: string[]; pct: number[][]; }

export interface OverviewData { kpi: Kpi; heat: Heat; trend: Trend; women: WomenShare[]; composition: Composition; genderTrend: GenderTrend; ageTrend: AgeTrend; by_source: Record<string, number>; }

export interface Kpi { records: number; races: number; series: number; minYear: number | null; maxYear: number | null; }
export function kpiStats(rows: SlimRecord[]): Kpi {
  const races = new Set<string>(), series = new Set<string>();
  let mn = Infinity, mx = -Infinity;
  for (const r of rows) {
    if (r.rk) races.add(r.rk);
    if (r.s) series.add(r.s);
    if (r.y != null) { mn = Math.min(mn, r.y); mx = Math.max(mx, r.y); }
  }
  return {
    records: rows.length, races: races.size, series: series.size,
    minYear: mn === Infinity ? null : mn, maxYear: mx === -Infinity ? null : mx,
  };
}

export interface Heat { years: number[]; cells: [number, number, number][]; max: number; }
export function monthYearHeat(rows: SlimRecord[]): Heat {
  const years = [...new Set(rows.filter((r) => r.y != null).map((r) => r.y as number))].sort((a, b) => a - b);
  const yi = new Map(years.map((y, i) => [y, i]));
  const grid = new Map<string, number>();
  for (const r of rows) {
    if (r.mon == null || r.y == null) continue;
    const k = `${r.mon}-${r.y}`;
    grid.set(k, (grid.get(k) || 0) + 1);
  }
  const cells: [number, number, number][] = [];
  let max = 0;
  for (const [k, c] of grid) {
    const [m, y] = k.split("-").map(Number);
    cells.push([m - 1, yi.get(y)!, c]);
    max = Math.max(max, c);
  }
  return { years, cells, max };
}

export interface Trend { years: number[]; series: string[]; counts: Record<string, number[]>; }
export function trendByYearSeries(rows: SlimRecord[], topN = 8): Trend {
  const years = [...new Set(rows.filter((r) => r.y != null).map((r) => r.y as number))].sort((a, b) => a - b);
  const yi = new Map(years.map((y, i) => [y, i]));
  const totals = new Map<string, number>();
  for (const r of rows) { const s = r.s || "其他"; totals.set(s, (totals.get(s) || 0) + 1); }
  const top = [...totals.entries()].sort((a, b) => b[1] - a[1]).slice(0, topN).map((e) => e[0]);
  const topSet = new Set(top);
  const counts: Record<string, number[]> = {};
  for (const s of [...top, "其他"]) counts[s] = years.map(() => 0);
  for (const r of rows) {
    if (r.y == null) continue;
    const s = r.s || "其他";
    const key = topSet.has(s) ? s : "其他";
    counts[key][yi.get(r.y)!]++;
  }
  if (counts["其他"].every((c) => c === 0)) delete counts["其他"];
  return { years, series: Object.keys(counts), counts };
}

export interface WomenShare { series: string; f: number; total: number; pct: number; }
export function womenShareBySeries(rows: SlimRecord[], minN = 50): WomenShare[] {
  const g = new Map<string, { f: number; t: number }>();
  for (const r of rows) {
    if (r.g !== "M" && r.g !== "F") continue;
    const s = r.s || "其他";
    const e = g.get(s) || { f: 0, t: 0 };
    if (r.g === "F") e.f++;
    e.t++;
    g.set(s, e);
  }
  return [...g.entries()]
    .filter(([, e]) => e.t >= minN)
    .map(([s, e]) => ({ series: s, f: e.f, total: e.t, pct: Math.round((100 * e.f) / e.t) }))
    .sort((a, b) => b.total - a.total);
}

export interface Composition { classes: string[]; male: number[]; female: number[]; unknown: number[]; }
export function compositionByClass(rows: SlimRecord[]): Composition {
  const g = new Map<string, { m: number; f: number; u: number }>();
  for (const r of rows) {
    const c = r.rc || "未分類";
    const e = g.get(c) || { m: 0, f: 0, u: 0 };
    if (r.g === "M") e.m++;
    else if (r.g === "F") e.f++;
    else e.u++;
    g.set(c, e);
  }
  const total = (c: string) => { const e = g.get(c)!; return e.m + e.f + e.u; };
  const classes = [...g.keys()].sort((a, b) => total(b) - total(a));
  return {
    classes,
    male: classes.map((c) => g.get(c)!.m),
    female: classes.map((c) => g.get(c)!.f),
    unknown: classes.map((c) => g.get(c)!.u),
  };
}
