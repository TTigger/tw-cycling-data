import type { AthleteDetail, AthleteHistoryRow } from "./types";

export interface CommonRace {
  rk: string; rn: string; y: number;
  aRank: number | null; bRank: number | null;
  aT: number | null; bT: number | null;
  winner: "a" | "b" | "tie";
}

export interface Comparison {
  common: CommonRace[];   // race-years both rode, newest first
  aWins: number; bWins: number; meets: number;
}

/** Each rider's best (lowest-rank) row per race-year, keyed "rk__year". */
function bestPerRaceYear(history: AthleteHistoryRow[]): Map<string, AthleteHistoryRow> {
  const m = new Map<string, AthleteHistoryRow>();
  for (const r of history) {
    if (r.y == null) continue;
    const k = `${r.rk}__${r.y}`;
    const cur = m.get(k);
    if (!cur || (r.rank ?? Infinity) < (cur.rank ?? Infinity)) m.set(k, r);
  }
  return m;
}

/**
 * Head-to-head comparison of two athletes: the race-years they both rode, who
 * placed better in each (lower rank wins; equal/unknown ranks are a tie), and
 * the overall win tally. Newest race-years first.
 */
export function compareAthletes(a: AthleteDetail, b: AthleteDetail): Comparison {
  const am = bestPerRaceYear(a.history);
  const bm = bestPerRaceYear(b.history);
  const common: CommonRace[] = [];
  let aWins = 0, bWins = 0;
  for (const [k, ar] of am) {
    const br = bm.get(k);
    if (!br) continue;
    let winner: "a" | "b" | "tie" = "tie";
    if (ar.rank != null && br.rank != null && ar.rank !== br.rank) {
      winner = ar.rank < br.rank ? "a" : "b";
    }
    if (winner === "a") aWins++;
    else if (winner === "b") bWins++;
    common.push({
      rk: ar.rk, rn: ar.rn, y: ar.y as number,
      aRank: ar.rank, bRank: br.rank, aT: ar.t, bT: br.t, winner,
    });
  }
  common.sort((x, y) => y.y - x.y || x.rn.localeCompare(y.rn));
  return { common, aWins, bWins, meets: common.length };
}
