import { describe, it, expect } from "vitest";
import { compareAthletes } from "./compare";
import type { AthleteDetail, AthleteHistoryRow } from "./types";

function h(p: Partial<AthleteHistoryRow>): AthleteHistoryRow {
  return { y: 2024, rk: "r", rn: "賽", cat: null, g: "M", ag: null, team: null,
           rank: 5, t: 3600, label: null, d: null, field: 100, ...p };
}
function det(id: string, history: AthleteHistoryRow[]): AthleteDetail {
  return { id, nm: id, conf: "high", has_uci: false, has_rider: true,
           teams: [], traits: {}, history };
}

describe("compareAthletes", () => {
  it("finds only race-years both rode and tallies wins by lower rank", () => {
    const a = det("A", [h({ rk: "x", y: 2024, rank: 2 }), h({ rk: "y", y: 2023, rank: 1 }),
                        h({ rk: "solo", y: 2022, rank: 1 })]);
    const b = det("B", [h({ rk: "x", y: 2024, rank: 5 }), h({ rk: "y", y: 2023, rank: 1 })]);
    const c = compareAthletes(a, b);
    expect(c.meets).toBe(2);                  // x-2024 and y-2023; solo excluded
    expect(c.common.map((r) => `${r.rk}${r.y}`)).toEqual(["x2024", "y2023"]); // newest first
    expect(c.aWins).toBe(1);                  // A beat B at x-2024
    expect(c.bWins).toBe(0);
    const tie = c.common.find((r) => r.rk === "y");
    expect(tie?.winner).toBe("tie");          // equal ranks -> tie
  });

  it("keeps each rider's best row when they have duplicates in a race-year", () => {
    const a = det("A", [h({ rk: "x", y: 2024, rank: 9 }), h({ rk: "x", y: 2024, rank: 3 })]);
    const b = det("B", [h({ rk: "x", y: 2024, rank: 5 })]);
    const c = compareAthletes(a, b);
    expect(c.meets).toBe(1);
    expect(c.common[0].aRank).toBe(3);        // A's best, not 9
    expect(c.aWins).toBe(1);                  // 3 < 5
  });

  it("returns no common races when careers never overlap", () => {
    const a = det("A", [h({ rk: "x", y: 2024 })]);
    const b = det("B", [h({ rk: "z", y: 2024 })]);
    expect(compareAthletes(a, b).meets).toBe(0);
  });
});
