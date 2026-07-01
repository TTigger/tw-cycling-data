import { describe, it, expect } from "vitest";
import { availableCohorts, pickDefaultCohort, availableGroups, pickDefaultGroup, parseFinishTime } from "./benchmark";
import type { BenchmarkRace } from "./types";

const race: BenchmarkRace = {
  rn: "賽事R",
  groups: {
    "130K": { years: [2024], cohorts: {
      all: { n: 100, type: "all", label: "全部完賽者", bp: [] },
      "age:40-49": { n: 60, type: "age", label: "40-49 歲", bp: [] },
    } },
    "50K": { years: [2024], cohorts: { all: { n: 40, type: "all", label: "全部完賽者", bp: [] } } },
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

describe("benchmark groups", () => {
  it("lists groups by size desc + default is largest", () => {
    expect(availableGroups(race).map((g) => g.label)).toEqual(["130K", "50K"]);
    expect(pickDefaultGroup(race)).toBe("130K");
  });
  it("cohorts operate within a group", () => {
    const g = race.groups["130K"];
    expect(availableCohorts(g).map((c) => c.key)).toEqual(["age:40-49", "all"]);
    expect(pickDefaultCohort(g)).toBe("age:40-49");
  });
});
