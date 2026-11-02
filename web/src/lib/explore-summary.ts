import { quantile } from "./aggregate";
import type { SlimRecord } from "./types";

export interface ExploreSummary {
  n: number; races: number; yMin: number | null; yMax: number | null;
  womenPct: number | null;     // among finishers with known gender
  /** Median/fastest only when the selection is one race: times across races
   * of different distances don't have a meaningful median. */
  median: number | null; fastest: number | null;
  group: string | null;        // division the median is quoted for (largest), null = single field
}

export function summarizeExplore(rows: SlimRecord[], oneRace: boolean): ExploreSummary {
  const races = new Set<string>();
  let yMin = Infinity, yMax = -Infinity, f = 0, known = 0;
  const byCat = new Map<string, number[]>();
  for (const r of rows) {
    races.add(r.rk);
    if (r.y != null) { if (r.y < yMin) yMin = r.y; if (r.y > yMax) yMax = r.y; }
    if (r.g) { known++; if (r.g === "F") f++; }
    if (oneRace && r.t != null) { const k = r.cat ?? ""; (byCat.get(k) ?? byCat.set(k, []).get(k)!).push(r.t); }
  }
  let group = "", ts: number[] = [];
  for (const [k, v] of byCat) if (v.length > ts.length) { group = k; ts = v; }
  ts.sort((a, b) => a - b);
  return {
    n: rows.length, races: races.size,
    yMin: yMin === Infinity ? null : yMin, yMax: yMax === -Infinity ? null : yMax,
    womenPct: known >= 30 ? Math.round((100 * f) / known) : null,
    median: ts.length ? quantile(ts, 0.5) : null, fastest: ts.length ? ts[0] : null,
    group: byCat.size > 1 ? group || "未標組別" : null,
  };
}
