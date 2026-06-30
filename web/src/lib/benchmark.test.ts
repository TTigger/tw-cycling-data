import { describe, it, expect } from "vitest";
import { availableCohorts, pickDefaultCohort, parseFinishTime } from "./benchmark";
import type { BenchmarkRace } from "./types";

const race: BenchmarkRace = {
  rn: "賽事R", years: [2024, 2025],
  cohorts: {
    all: { n: 100, type: "all", label: "全部完賽者", bp: [] },
    "age:40-49": { n: 60, type: "age", label: "40-49 歲", bp: [] },
    "age:40-49|g:M": { n: 50, type: "age", label: "40-49 歲 男", bp: [] },
    "cat:菁英": { n: 30, type: "cat", label: "菁英", bp: [] },
  },
};

describe("parseFinishTime", () => {
  it("accepts HH:MM:SS, MM:SS, and plain seconds; rejects junk", () => {
    expect(parseFinishTime("01:00:00")).toBe(3600);
    expect(parseFinishTime("45:30")).toBe(2730);
    expect(parseFinishTime("90")).toBe(90);
    expect(parseFinishTime("nope")).toBeNull();
    expect(parseFinishTime("")).toBeNull();
  });
});

describe("benchmark cohort selection", () => {
  it("orders cohorts: age|gender, age, cat, all", () => {
    const keys = availableCohorts(race).map((c) => c.key);
    expect(keys).toEqual(["age:40-49|g:M", "age:40-49", "cat:菁英", "all"]);
  });
  it("defaults to a plain age cohort when present", () => {
    expect(pickDefaultCohort(race)).toBe("age:40-49");
  });
  it("falls back to cat then all", () => {
    const noAge: BenchmarkRace = { rn: "x", years: [2024],
      cohorts: { all: { n: 40, type: "all", label: "全部", bp: [] },
                 "cat:挑戰": { n: 25, type: "cat", label: "挑戰", bp: [] } } };
    expect(pickDefaultCohort(noAge)).toBe("cat:挑戰");
    const onlyAll: BenchmarkRace = { rn: "y", years: [2024],
      cohorts: { all: { n: 40, type: "all", label: "全部", bp: [] } } };
    expect(pickDefaultCohort(onlyAll)).toBe("all");
  });
});
