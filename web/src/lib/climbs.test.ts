import { describe, it, expect } from "vitest";
import { isClimbRace, climbRaces } from "./climbs";
import type { RaceIndex } from "./types";

function r(p: Partial<RaceIndex>): RaceIndex {
  return { rk: "k", y: 2025, rn: "賽", s: "S", rows: 100, multi_year: false, has_team: false, file: "k__2025", ...p };
}

describe("isClimbRace", () => {
  it("matches legendary climbs by name", () => {
    expect(isClimbRace("2025 TIS崇越盃武嶺自行車挑戰賽")).toBe(true);
    expect(isClimbRace("臺灣KOM登山王之路-春季")).toBe(true);
    expect(isClimbRace("臺灣KOM太平洋經典賽")).toBe(true);
    expect(isClimbRace("96聯賽武嶺站")).toBe(true);
    expect(isClimbRace("環花東國際自行車賽")).toBe(false);
    expect(isClimbRace(null)).toBe(false);
  });
});

describe("climbRaces", () => {
  it("filters + sorts by year desc then rows desc", () => {
    const list = climbRaces([
      r({ rn: "武嶺A", y: 2024, rows: 100 }),
      r({ rn: "武嶺B", y: 2025, rows: 50 }),
      r({ rn: "環花東", y: 2025, rows: 999 }),
    ]);
    expect(list.map((x) => x.rn)).toEqual(["武嶺B", "武嶺A"]);
  });
});
