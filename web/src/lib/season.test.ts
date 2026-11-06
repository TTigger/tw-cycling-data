import { describe, it, expect } from "vitest";
import { buildSeason, isRealGap, seasonYears, shortDate } from "./season";
import type { RaceIndex, CoverageGap } from "./types";

const race = (rk: string, y: number, d: string | null, rows = 100): RaceIndex => ({
  rk, y, rn: rk, s: null, rows, multi_year: false, has_team: false, file: `${rk}__${y}`, d,
});

describe("buildSeason", () => {
  const races = [
    race("銅礦88", 2026, "2026-03-21", 255),
    race("96台北站", 2026, "2026-05-10", 232),
    race("環大苗栗", 2026, null, 60),
    race("去年的賽", 2025, "2025-09-08"),
  ];
  const gaps: CoverageGap[] = [
    { race: "96苗栗站", calendar: "c", guess_source: "", status: "NOT_INGESTED", date: "2026-10-18" },
    { race: "太平洋盃", calendar: "c", guess_source: "", status: "NOT_HELD", date: "2026-12-04" },
    { race: "已過的未辦", calendar: "c", guess_source: "", status: "NOT_HELD", date: "2026-10-01" },
    { race: "某平台", calendar: "c", guess_source: "", status: "BLOCKED", date: "2026-07-01" },
    { race: "無排名", calendar: "c", guess_source: "", status: "NO_RANKING", date: "2026-06-01" },
    { race: "沒日期", calendar: "c", guess_source: "", status: "NOT_INGESTED" },
    { race: "去年缺", calendar: "c", guess_source: "", status: "NOT_INGESTED", date: "2025-10-01" },
  ];
  const s = buildSeason(races, gaps, 2026, "2026-11-02");

  it("merges ingested races and gaps for the year, newest first", () => {
    expect(s.items.map((i) => i.name)).toEqual(
      ["太平洋盃", "96苗栗站", "已過的未辦", "某平台", "96台北站", "銅礦88"]);
  });
  it("maps statuses and corrects stale not-held", () => {
    const by = Object.fromEntries(s.items.map((i) => [i.name, i.status]));
    expect(by["銅礦88"]).toBe("ok");
    expect(by["96苗栗站"]).toBe("wait");
    expect(by["太平洋盃"]).toBe("soon");
    expect(by["已過的未辦"]).toBe("wait");
    expect(by["某平台"]).toBe("miss");
  });
  it("keeps undated ingested races aside and counts everything", () => {
    expect(s.undated.map((i) => i.name)).toEqual(["環大苗栗"]);
    expect(s.counts).toEqual({ ok: 3, wait: 2, miss: 1, soon: 1 });
  });
  it("buckets by month, oldest first within a month", () => {
    expect(s.months[2].items.map((i) => i.name)).toEqual(["銅礦88"]);
    expect(s.months[9].items.map((i) => i.name)).toEqual(["已過的未辦", "96苗栗站"]);
    expect(s.months.reduce((n, m) => n + m.items.length, 0)).toBe(s.items.length);
  });
});

describe("seasonYears / shortDate", () => {
  it("lists years newest first", () => {
    expect(seasonYears([race("a", 2024, null), race("b", 2026, null), race("c", 2024, null)]))
      .toEqual([2026, 2024]);
  });
  it("formats MM/DD", () => {
    expect(shortDate("2026-09-07")).toBe("09/07");
    expect(shortDate(null)).toBe("—");
  });
});

describe("isRealGap", () => {
  it("counts only races whose results are missing", () => {
    expect(isRealGap({ status: "NOT_INGESTED" })).toBe(true);
    expect(isRealGap({ status: "BLOCKED" })).toBe(true);
    expect(isRealGap({ status: undefined })).toBe(true);
    expect(isRealGap({ status: "NO_RANKING" })).toBe(false);
    expect(isRealGap({ status: "NOT_HELD" })).toBe(false);
  });
});
