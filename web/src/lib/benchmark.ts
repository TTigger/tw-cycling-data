import type { BenchmarkRace, BenchmarkGroup } from "./types";

/** Distance/event groups within a race, largest (by `all` count) first. */
export function availableGroups(race: BenchmarkRace) {
  return Object.entries(race.groups)
    .map(([label, group]) => ({ label, group, n: group.cohorts.all?.n ?? 0 }))
    .sort((a, b) => b.n - a.n);
}

/** Default group: the largest one. */
export function pickDefaultGroup(race: BenchmarkRace): string {
  return availableGroups(race)[0]?.label ?? "";
}

/** Cohorts within a group, most-specific first: age|gender, age, cat, all. */
export function availableCohorts(group: BenchmarkGroup) {
  const rank = (key: string, type: string) =>
    type === "age" && key.includes("|g:") ? 0 : type === "age" ? 1 : type === "cat" ? 2 : 3;
  return Object.entries(group.cohorts)
    .map(([key, cohort]) => ({ key, cohort }))
    .sort((a, b) => rank(a.key, a.cohort.type) - rank(b.key, b.cohort.type)
      || b.cohort.n - a.cohort.n);
}

/** Default cohort key within a group: plain age band, else category, else all. */
export function pickDefaultCohort(group: BenchmarkGroup): string {
  const c = group.cohorts;
  const plainAge = Object.keys(c).find((k) => c[k].type === "age" && !k.includes("|g:"));
  if (plainAge) return plainAge;
  const cat = Object.keys(c).find((k) => c[k].type === "cat");
  if (cat) return cat;
  return "all";
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
