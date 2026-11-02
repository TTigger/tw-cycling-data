import type { RaceIndex, CoverageGap } from "./types";

/** ok = results in the dataset · wait = held, results not in yet ·
 * miss = results exist on a platform we can't read · soon = not held yet. */
export type SeasonStatus = "ok" | "wait" | "miss" | "soon";

export interface SeasonItem {
  key: string;
  name: string;
  date: string | null;        // YYYY-MM-DD
  status: SeasonStatus;
  rows?: number;              // finishers, for ingested races
  file?: string;              // race page slug, for ingested races
  series?: string | null;
  note?: string;
}

export interface SeasonMonth { month: number; items: SeasonItem[]; }

export interface Season {
  year: number;
  /** Dated races, newest first. */
  items: SeasonItem[];
  /** Ingested race-years whose source gave no date. */
  undated: SeasonItem[];
  months: SeasonMonth[];
  counts: Record<SeasonStatus, number>;
}

// discover.py triage status -> board status. Statuses not listed here
// (NO_RANKING, OTHER_LEAGUE, COLLECTED…) are not shown: either nothing to
// collect, or already in the data under another name.
const GAP_STATUS: Record<string, SeasonStatus> = {
  NOT_INGESTED: "wait", HELD_UNCHECKED: "wait", BLOCKED: "miss", NOT_HELD: "soon",
};

const DATE = /^\d{4}-\d{2}-\d{2}$/;

/** Years that have ingested races, newest first. */
export function seasonYears(races: RaceIndex[]): number[] {
  return [...new Set(races.map((r) => r.y).filter((y): y is number => typeof y === "number"))]
    .sort((a, b) => b - a);
}

/** Lay one year's races out for the home season board: ingested race-years from
 * races.json plus the known-but-missing races from coverage.json's gaps. */
export function buildSeason(races: RaceIndex[], gaps: CoverageGap[], year: number,
                            today: string): Season {
  const items: SeasonItem[] = [];
  const undated: SeasonItem[] = [];
  for (const r of races) {
    if (r.y !== year) continue;
    const it: SeasonItem = { key: `r:${r.file}`, name: r.rn, date: r.d && DATE.test(r.d) ? r.d : null,
                             status: "ok", rows: r.rows, file: r.file, series: r.s };
    (it.date ? items : undated).push(it);
  }
  for (const g of gaps) {
    let status = g.status ? GAP_STATUS[g.status] : undefined;
    if (!status || !g.date || !DATE.test(g.date) || Number(g.date.slice(0, 4)) !== year) continue;
    // calendars are re-checked weekly; keep the board honest between runs
    if (status === "soon" && g.date < today) status = "wait";
    if (status === "wait" && g.date >= today) status = "soon";
    items.push({ key: `g:${g.race}|${g.date}`, name: g.race, date: g.date, status, note: g.note });
  }
  items.sort((a, b) => (b.date! < a.date! ? -1 : b.date! > a.date! ? 1 : a.name.localeCompare(b.name)));
  undated.sort((a, b) => (b.rows ?? 0) - (a.rows ?? 0));

  const months: SeasonMonth[] = Array.from({ length: 12 }, (_, i) => ({ month: i + 1, items: [] }));
  for (const it of items) months[Number(it.date!.slice(5, 7)) - 1].items.push(it);
  for (const m of months) m.items.reverse();          // oldest first inside a month

  const counts: Record<SeasonStatus, number> = { ok: 0, wait: 0, miss: 0, soon: 0 };
  for (const it of [...items, ...undated]) counts[it.status]++;
  return { year, items, undated, months, counts };
}

/** Short "MM/DD" for list rows. */
export function shortDate(d: string | null): string {
  return d ? `${d.slice(5, 7)}/${d.slice(8, 10)}` : "—";
}
