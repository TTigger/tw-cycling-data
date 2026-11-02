import { describe, it, expect } from "vitest";
import { summarizeTrends } from "./trends-summary";

const gt = { years: [2009, 2011, 2025, 2026], f: [47, 1, 3887, 1836], known: [1016, 10, 24915, 10717] };
const at = { years: [2009, 2025, 2026], bands: ["U19", "30-39", "40-49"],
             pct: [[2, 7, 38], [46, 25, 21], [26, 36, 17]] };

describe("summarizeTrends", () => {
  const s = summarizeTrends(gt, at, 2026);
  it("compares first usable year with the last finished season", () => {
    expect(s.women).toEqual({ from: 2009, to: 2025, fromPct: 5, toPct: 16 });
  });
  it("finds the age band that grew and shrank most, and the largest one", () => {
    expect(s.ageUp).toMatchObject({ band: "40-49", fromPct: 26, toPct: 36 });
    expect(s.ageDown).toMatchObject({ band: "30-39", fromPct: 46, toPct: 25 });
    expect(s.ageTop).toEqual({ band: "40-49", year: 2025, pct: 36 });
  });
  it("returns nulls when there is too little data", () => {
    const e = summarizeTrends({ years: [2026], f: [1], known: [100] }, { years: [], bands: [], pct: [] }, 2026);
    expect(e).toEqual({ women: null, ageUp: null, ageDown: null, ageTop: null });
  });
});
