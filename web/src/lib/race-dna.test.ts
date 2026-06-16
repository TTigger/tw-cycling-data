import { describe, it, expect } from "vitest";
import { dnaFor, dnaRadarValues, dnaRaceList, similarRaces, dnaDistance, DNA_AXES } from "./race-dna";
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

describe("dnaDistance", () => {
  it("is zero for identical fingerprints", () => {
    expect(dnaDistance(ax(), ax())).toBe(0);
  });
  it("grows with axis differences", () => {
    expect(dnaDistance(ax(), ax({ size: 100 }))).toBeGreaterThan(0);
  });
});

describe("similarRaces", () => {
  const FILE2: RaceDnaFile = {
    target: { name: "目標賽", years: { "2024": ax({ climb: 50, size: 50 }) } },
    twin: { name: "雙胞賽", years: { "2024": ax({ climb: 50, size: 50 }) } },     // identical -> 100%
    near: { name: "相近賽", years: { "2024": ax({ climb: 55, size: 52 }) } },     // dist ~5.4
    // two editions: 2023 is wildly different, 2024 is moderately close but still
    // farther than `near` — so dedup must pick 2024 and it must rank after `near`
    multi: { name: "多屆賽", years: {
      "2023": ax({ climb: 0, size: 100, sel: 0, prest: 100, repeat: 0, women: 100 }),
      "2024": ax({ climb: 65, size: 60 }), // dist ~18
    } },
  };

  it("ranks the identical race top at 100% and excludes the target's own editions", () => {
    const out = similarRaces(FILE2, "target", 2024);
    expect(out[0].rk).toBe("twin");
    expect(out[0].sim).toBe(100);
    expect(out.some((r) => r.rk === "target")).toBe(false);
  });
  it("orders nearer races before farther ones", () => {
    const out = similarRaces(FILE2, "target", 2024);
    const idxNear = out.findIndex((r) => r.rk === "near");
    const idxMulti = out.findIndex((r) => r.rk === "multi");
    expect(idxNear).toBeLessThan(idxMulti);
  });
  it("keeps each other race's single closest edition (dedup by rk)", () => {
    const out = similarRaces(FILE2, "target", 2024);
    expect(out.filter((r) => r.rk === "multi")).toHaveLength(1);
    expect(out.find((r) => r.rk === "multi")?.year).toBe("2024"); // the closer edition
  });
  it("caps at k and returns empty when target is missing", () => {
    expect(similarRaces(FILE2, "target", 2024, 1)).toHaveLength(1);
    expect(similarRaces(FILE2, "ghost", 2024)).toEqual([]);
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
