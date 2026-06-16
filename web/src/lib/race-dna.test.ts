import { describe, it, expect } from "vitest";
import { dnaFor, dnaRadarValues, dnaRaceList, DNA_AXES } from "./race-dna";
import type { RaceDnaFile, RaceDnaAxes } from "./types";

const ax = (p: Partial<RaceDnaAxes> = {}): RaceDnaAxes => ({
  n: 100, sel: 50, size: 60, climb: 70, prest: 40, repeat: 30, women: 20, ...p,
});

const FILE: RaceDnaFile = {
  wuling: { name: "武嶺", years: { "2024": ax({ climb: 95 }), "2023": ax({ climb: 90 }) } },
  flat: { name: "繞圈賽", years: { "2024": ax({ climb: 10 }) } },
};

describe("dnaFor", () => {
  it("looks up a race-year's axes", () => {
    expect(dnaFor(FILE, "wuling", 2024)?.climb).toBe(95);
    expect(dnaFor(FILE, "wuling", "2023")?.climb).toBe(90);
  });
  it("returns null on misses and null year", () => {
    expect(dnaFor(FILE, "wuling", 2099)).toBeNull();
    expect(dnaFor(FILE, "ghost", 2024)).toBeNull();
    expect(dnaFor(FILE, "wuling", null)).toBeNull();
  });
});

describe("dnaRadarValues", () => {
  it("emits values in DNA_AXES order", () => {
    const v = dnaRadarValues(ax({ sel: 1, size: 2, climb: 3, prest: 4, repeat: 5, women: 6 }));
    expect(v).toEqual([1, 2, 3, 4, 5, 6]);
    expect(v).toHaveLength(DNA_AXES.length);
  });
});

describe("dnaRaceList", () => {
  it("flattens every fingerprinted race-year with a label", () => {
    const list = dnaRaceList(FILE);
    expect(list).toHaveLength(3); // wuling x2 + flat x1
    expect(list.every((o) => o.label === `${o.year} ${o.name}`)).toBe(true);
    // same race: newer year first
    const wuling = list.filter((o) => o.rk === "wuling");
    expect(wuling.map((o) => o.year)).toEqual(["2024", "2023"]);
  });
});
