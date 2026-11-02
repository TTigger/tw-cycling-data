import { describe, it, expect } from "vitest";
import { summarizeExplore } from "./explore-summary";
import type { SlimRecord } from "./types";

const rec = (rk: string, y: number, g: "M" | "F" | null, t: number | null): SlimRecord =>
  ({ rk, y, mon: null, s: null, rc: null, cat: null, g, ag: null, t, rank: null, dist: null, spd: null, plat: null, reg: null });

describe("summarizeExplore", () => {
  const rows = [...Array(30)].map((_, i) => rec(i % 2 ? "a" : "b", 2020 + (i % 3), i < 6 ? "F" : "M", 100 + i));
  it("counts rows, races, years and women share", () => {
    expect(summarizeExplore(rows, false)).toEqual(
      { n: 30, races: 2, yMin: 2020, yMax: 2022, womenPct: 20, median: null, fastest: null, group: null });
  });
  it("adds median and fastest for a single race only", () => {
    const s = summarizeExplore([rec("a", 2024, null, 300), rec("a", 2024, null, 100), rec("a", 2024, null, 200)], true);
    expect(s).toMatchObject({ median: 200, fastest: 100, womenPct: null, group: null });
  });
  it("quotes the largest division when a race has several courses", () => {
    const c = (t: number, cat: string) => ({ ...rec("a", 2024, null, t), cat });
    const s = summarizeExplore([c(500, "112K"), c(600, "112K"), c(700, "112K"), c(100, "30K")], true);
    expect(s).toMatchObject({ group: "112K", median: 600, fastest: 500 });
  });
});
