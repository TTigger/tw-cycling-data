import { describe, it, expect } from "vitest";
import { calibratedSeries, calibratableRaces, raceSeverity, raceSeverityAll } from "./difficulty";
import type { AthleteHistoryRow, RaceDifficultyFile, RaceDifficulty } from "./types";

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

describe("raceSeverity", () => {
  const diff: RaceDifficulty = {
    name: "某盃", baseline: 10000,
    years: {
      "2022": { median: 10000, coeff: 1.0, n: 1000 },
      "2023": { median: 12000, coeff: 1.2, n: 400 },   // far fewer + slower
      "2024": { median: 9500, coeff: 0.95, n: 1100 },  // more + faster
    },
  };
  it("flags 嚴苛 when an edition had far fewer finishers AND slower times", () => {
    const s = raceSeverity(diff, 2023)!;
    expect(s.baselineN).toBe(1000);          // median(1000,400,1100)
    expect(s.finisherDelta).toBe(-60);       // 400 vs 1000
    expect(s.timeDelta).toBe(20);            // coeff 1.2
    expect(s.verdict).toBe("嚴苛");
  });
  it("flags 偏易 when more finishers and faster", () => {
    expect(raceSeverity(diff, 2024)!.verdict).toBe("偏易");
  });
  it("is 正常 for a typical year and null for a missing/absent year", () => {
    expect(raceSeverity(diff, 2022)!.verdict).toBe("正常");
    expect(raceSeverity(diff, 2099)).toBeNull();
    expect(raceSeverity(undefined, 2022)).toBeNull();
  });
  it("lists all covered years newest-first", () => {
    expect(raceSeverityAll(diff).map((s) => s.year)).toEqual([2024, 2023, 2022]);
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
