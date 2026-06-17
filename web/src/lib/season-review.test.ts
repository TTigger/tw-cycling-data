import { describe, it, expect } from "vitest";
import { seasonRecap } from "./season-review";
import type { AthleteDetail, AthleteHistoryRow, ClimbVamEntry } from "./types";

function h(p: Partial<AthleteHistoryRow>): AthleteHistoryRow {
  return { y: 2024, rk: "r", rn: "賽", cat: null, g: "M", ag: null, team: null,
    rank: 5, t: 3600, label: null, d: "2024-05-01", field: 100, ...p };
}
const D: AthleteDetail = {
  id: "a", nm: "王○明", conf: "high", has_uci: false, has_rider: true, teams: [],
  traits: { climb: { pct: 80, n: 5 }, road: { pct: 60, n: 4 }, crit: { pct: 62, n: 2 } },
  history: [
    h({ y: 2023, rk: "x", rank: 50, field: 100 }),                         // 2023 median 50
    h({ y: 2024, rk: "x", rn: "武嶺", rank: 1, field: 100, d: "2024-03-02" }), // pct 99, win
    h({ y: 2024, rk: "y", rn: "繞圈", rank: 30, field: 100, d: "2024-03-20" }),// pct 70
  ],
};
const VAM: ClimbVamEntry[] = [
  { id: "a", nm: "王○明", best_vam: 1150, best_wkg: 4, climb: "武嶺", y: 2024, conf: "high", g: "M" },
];

describe("seasonRecap", () => {
  const r = seasonRecap(D, 2024, VAM);
  it("aggregates the season", () => {
    expect(r.races).toBe(2);
    expect(r.medianPct).toBe(85);             // median(99,70) = 84.5 -> 85
    expect(r.wins).toBe(1);
    expect(r.best?.rn).toBe("武嶺");          // highest pct (99)
    expect(r.bestVam?.value).toBe(1150);
    expect(r.busiestMonth).toBe(3);           // both 2024 rides in March
    expect(r.archetype).toBe("爬坡型");
  });
  it("computes improvement vs the previous season", () => {
    expect(r.deltaVsPrev).toBe(35);           // 85 (2024) - 50 (2023)
  });
  it("null delta when no previous season", () => {
    expect(seasonRecap(D, 2023, VAM).deltaVsPrev).toBeNull();
  });
});
