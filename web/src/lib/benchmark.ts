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

/** Default cohort key: a plain age band if present, else a category, else all. */
export function pickDefaultCohort(race: BenchmarkRace): string {
  const c = race.cohorts;
  const plainAge = Object.keys(c).find((k) => c[k].type === "age" && !k.includes("|g:"));
  if (plainAge) return plainAge;
  const cat = Object.keys(c).find((k) => c[k].type === "cat");
  if (cat) return cat;
  return "all";
}
