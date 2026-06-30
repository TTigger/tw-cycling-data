import type { BenchmarkRace } from "./types";

/** Cohorts a user can pick, most-specific first: age|gender, age, cat, all. */
export function availableCohorts(race: BenchmarkRace) {
  const rank = (key: string, type: string) =>
    type === "age" && key.includes("|g:") ? 0 : type === "age" ? 1 : type === "cat" ? 2 : 3;
  return Object.entries(race.cohorts)
    .map(([key, cohort]) => ({ key, cohort }))
    .sort((a, b) => rank(a.key, a.cohort.type) - rank(b.key, b.cohort.type)
      || b.cohort.n - a.cohort.n);
}

/** Parse a finish time the user typed: HH:MM:SS, MM:SS, or plain seconds.
 * Mirrors the MCP server's hms_to_seconds so the web tool and the MCP tool
 * accept the same inputs. Returns null on anything unparseable. */
export function parseFinishTime(s: string): number | null {
  const t = (s ?? "").trim();
  if (!t) return null;
  if (t.includes(":")) {
    const parts = t.split(":").map((p) => Number(p));
    if (parts.some((n) => !Number.isInteger(n) || n < 0)) return null;
    if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
    if (parts.length === 2) return parts[0] * 60 + parts[1];
    return null;
  }
  const n = Number(t);
  return Number.isInteger(n) && n >= 0 ? n : null;
}

/** Default cohort key: a plain age band if present, else a category, else all. */
export function pickDefaultCohort(race: BenchmarkRace): string {
  const c = race.cohorts;
  const plainAge = Object.keys(c).find((k) => c[k].type === "age" && !k.includes("|g:"));
  if (plainAge) return plainAge;
  const cat = Object.keys(c).find((k) => c[k].type === "cat");
  if (cat) return cat;
  return "all";
}
