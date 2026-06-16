import { describe, it, expect } from "vitest";
import { calibratedSeries, calibratableRaces } from "./difficulty";
import type { AthleteHistoryRow, RaceDifficultyFile } from "./types";

function h(p: Partial<AthleteHistoryRow>): AthleteHistoryRow {
  return { y: 2024, rk: "r", rn: "賽", cat: null, g: "M", ag: null, team: null,
           rank: 5, t: 3600, label: null, d: null, field: 100, ...p };
}

const DIFF: RaceDifficultyFile = {
  wuling: {
    name: "武嶺", baseline: 10000,
    years: {
      "2023": { median: 12000, coeff: 1.2, n: 80 }, // hard year
      "2024": { median: 8000, coeff: 0.8, n: 90 },  // easy year
    },
  },
  solo: { name: "單年賽", baseline: 5000, years: { "2024": { median: 5000, coeff: 1, n: 50 } } },
};

describe("calibratedSeries", () => {
  it("calibrates raw time by dividing out the year's difficulty coeff", () => {
    const hist = [h({ rk: "wuling", y: 2023, t: 12000 }), h({ rk: "wuling", y: 2024, t: 8000 })];
    const s = calibratedSeries(hist, "wuling", DIFF.wuling);
    expect(s.map((p) => p.y)).toEqual([2023, 2024]);
    // identical "average" rides both calibrate to ~10000 despite different raw times
    expect(s[0].calibrated).toBe(10000); // 12000 / 1.2
    expect(s[1].calibrated).toBe(10000); // 8000 / 0.8
  });
  it("keeps the fastest row when a rider has duplicates in one race-year", () => {
    const hist = [h({ rk: "wuling", y: 2024, t: 9000 }), h({ rk: "wuling", y: 2024, t: 8000 })];
    const s = calibratedSeries(hist, "wuling", DIFF.wuling);
    expect(s).toHaveLength(1);
    expect(s[0].raw).toBe(8000);
  });
  it("skips years missing from the difficulty table or without a time", () => {
    const hist = [h({ rk: "wuling", y: 2023, t: 12000 }), h({ rk: "wuling", y: 2025, t: 9000 }),
                  h({ rk: "wuling", y: 2024, t: null })];
    const s = calibratedSeries(hist, "wuling", DIFF.wuling);
    expect(s.map((p) => p.y)).toEqual([2023]); // 2025 not in table, 2024 has no time
  });
  it("returns empty when the race has no difficulty data", () => {
    expect(calibratedSeries([h({ rk: "x", y: 2024, t: 1 })], "x", undefined)).toEqual([]);
  });
});

describe("calibratableRaces", () => {
  it("lists only races ridden in >=2 covered years", () => {
    const hist = [
      h({ rk: "wuling", y: 2023, t: 12000 }), h({ rk: "wuling", y: 2024, t: 8000 }),
      h({ rk: "solo", y: 2024, t: 5000 }),    // single covered year -> excluded
    ];
    const out = calibratableRaces(hist, DIFF);
    expect(out.map((r) => r.rk)).toEqual(["wuling"]);
    expect(out[0].n).toBe(2);
    expect(out[0].name).toBe("武嶺");
  });
});
