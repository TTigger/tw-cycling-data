import type { SlimRecord } from "./types";

export function quantile(sorted: number[], q: number): number {
  if (sorted.length === 0) return NaN;
  if (sorted.length === 1) return sorted[0];
  const pos = (sorted.length - 1) * q;
  const base = Math.floor(pos);
  const rest = pos - base;
  const next = sorted[base + 1];
  return next !== undefined ? sorted[base] + rest * (next - sorted[base]) : sorted[base];
}

export interface Bin { x0: number; x1: number; count: number; }
export function histogram(values: number[], binSeconds: number): Bin[] {
  const v = values.filter((x) => Number.isFinite(x));
  if (!v.length || binSeconds <= 0) return [];
  const min = Math.min(...v);
  const max = Math.max(...v);
  const start = Math.floor(min / binSeconds) * binSeconds;
  const bins: Bin[] = [];
  for (let x = start; x <= max; x += binSeconds) bins.push({ x0: x, x1: x + binSeconds, count: 0 });
  for (const x of v) {
    const i = Math.min(bins.length - 1, Math.floor((x - start) / binSeconds));
    bins[i].count++;
  }
  return bins;
}

export interface Box { group: string; min: number; q1: number; median: number; q3: number; max: number; n: number; }
export function boxByGroup(rows: { ag: string | null; t: number | null }[], minN = 8): Box[] {
  const groups = new Map<string, number[]>();
  for (const r of rows) {
    if (r.ag == null || r.t == null) continue;
    const a = groups.get(r.ag) || [];
    a.push(r.t);
    groups.set(r.ag, a);
  }
  const out: Box[] = [];
  for (const [g, arr] of groups) {
    if (arr.length < minN) continue;
    arr.sort((a, b) => a - b);
    out.push({
      group: g, n: arr.length, min: arr[0], max: arr[arr.length - 1],
      q1: quantile(arr, 0.25), median: quantile(arr, 0.5), q3: quantile(arr, 0.75),
    });
  }
  return out.sort((a, b) => a.group.localeCompare(b.group));
}

export interface Spread { key: string; rk: string; y: number | null; winner: number; median: number; ratio: number; n: number; }
export function raceSpread(
  rows: { rk: string; y: number | null; t: number | null; rc: string | null; s: string | null }[],
  minN = 10,
): Spread[] {
  const g = new Map<string, { rk: string; y: number | null; ts: number[] }>();
  for (const r of rows) {
    if (r.t == null) continue;
    if (r.rc === "認證" || r.rc === "電輔車") continue;
    if (r.s != null && /認證|雙塔|北高|四極/.test(r.s)) continue;
    const k = `${r.rk}__${r.y}`;
    const e = g.get(k) || { rk: r.rk, y: r.y, ts: [] };
    e.ts.push(r.t);
    g.set(k, e);
  }
  const out: Spread[] = [];
  for (const [k, e] of g) {
    if (e.ts.length < minN) continue;
    e.ts.sort((a, b) => a - b);
    const winner = e.ts[0];
    const median = quantile(e.ts, 0.5);
    out.push({ key: k, rk: e.rk, y: e.y, winner, median, ratio: winner > 0 ? median / winner : 0, n: e.ts.length });
  }
  return out.sort((a, b) => b.ratio - a.ratio);
}

export interface ScatterPt { dist: number; spd: number; rc: string | null; }
export function distSpeedPoints(rows: { dist: number | null; spd: number | null; rc: string | null }[]): ScatterPt[] {
  const out: ScatterPt[] = [];
  for (const r of rows) if (r.dist != null && r.spd != null) out.push({ dist: r.dist, spd: r.spd, rc: r.rc });
  return out;
}

export interface Facets { years: number[]; series: string[]; raceClasses: string[]; genders: string[]; ageGroups: string[]; }
export function facetOptions(rows: SlimRecord[]): Facets {
  const years = new Set<number>(), series = new Set<string>(), rc = new Set<string>(),
        g = new Set<string>(), ag = new Set<string>();
  for (const r of rows) {
    if (r.y != null) years.add(r.y);
    if (r.s) series.add(r.s);
    if (r.rc) rc.add(r.rc);
    if (r.g) g.add(r.g);
    if (r.ag) ag.add(r.ag);
  }
  return {
    years: [...years].sort((a, b) => a - b),
    series: [...series].sort(),
    raceClasses: [...rc].sort(),
    genders: [...g].sort(),
    ageGroups: [...ag].sort(),
  };
}
