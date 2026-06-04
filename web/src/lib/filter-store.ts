import { map } from "nanostores";
import type { SlimRecord } from "./types";

export interface Filters {
  year: number | null; series: string | null; race: string | null;
  raceClass: string | null; gender: "M" | "F" | null; ageGroup: string | null;
}
export const EMPTY: Filters = {
  year: null, series: null, race: null, raceClass: null, gender: null, ageGroup: null,
};
export const $filters = map<Filters>({ ...EMPTY });

export function setFilter<K extends keyof Filters>(k: K, v: Filters[K]) {
  $filters.setKey(k, v);
  syncToUrl();
}

export function applyFilters(rows: SlimRecord[], f: Filters): SlimRecord[] {
  return rows.filter((r) =>
    (f.year == null || r.y === f.year) &&
    (f.series == null || r.s === f.series) &&
    (f.race == null || r.rk === f.race) &&
    (f.raceClass == null || r.rc === f.raceClass) &&
    (f.gender == null || r.g === f.gender) &&
    (f.ageGroup == null || r.ag === f.ageGroup)
  );
}

function syncToUrl() {
  if (typeof window === "undefined") return;
  const f = $filters.get();
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(f)) if (v != null) p.set(k, String(v));
  const qs = p.toString();
  history.replaceState(null, "", qs ? `?${qs}` : location.pathname);
}

export function hydrateFromUrl() {
  if (typeof window === "undefined") return;
  const p = new URLSearchParams(location.search);
  const next: Filters = { ...EMPTY };
  if (p.get("year")) next.year = Number(p.get("year"));
  next.series = p.get("series");
  next.race = p.get("race");
  next.raceClass = p.get("raceClass");
  const g = p.get("gender");
  next.gender = g === "M" || g === "F" ? g : null;
  next.ageGroup = p.get("ageGroup");
  $filters.set(next);
}
