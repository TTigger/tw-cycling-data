import { describe, it, expect } from "vitest";
import { percentileInField, searchAthletes, careerSummary, progression } from "./athletes";
import type { AthleteIndexEntry, AthleteDetail, AthleteHistoryRow } from "./types";

function a(p: Partial<AthleteIndexEntry>): AthleteIndexEntry {
  return { id: "x", nm: "王○明", n: 3, ny: 2, nr: 3, y0: 2023, y1: 2025, best: 5, conf: "high", uci: false, rid: false, ...p };
}
function h(p: Partial<AthleteHistoryRow>): AthleteHistoryRow {
  return { y: 2024, rk: "r", rn: "賽", cat: "M30", g: "M", ag: "30", team: "A隊", rank: 5, t: 3600, label: null, d: "2024-05-01", field: 100, ...p };
}

describe("percentileInField", () => {
  it("percent of field beaten", () => {
    expect(percentileInField(1, 100)).toBe(99);
    expect(percentileInField(50, 100)).toBe(50);
    expect(percentileInField(100, 100)).toBe(0);
  });
  it("null on missing/invalid", () => {
    expect(percentileInField(null, 100)).toBeNull();
    expect(percentileInField(5, null)).toBeNull();
    expect(percentileInField(5, 0)).toBeNull();
  });
});

describe("searchAthletes", () => {
  const list = [
    a({ id: "1", nm: "王○明", n: 10 }),
    a({ id: "2", nm: "王○華", n: 3 }),
    a({ id: "3", nm: "李○", n: 20 }),
  ];
  it("substring match on masked name", () => {
    const r = searchAthletes(list, "王");
    expect(r.map((x) => x.id)).toEqual(["1", "2"]);
  });
  it("empty query returns all, most-tracked first", () => {
    expect(searchAthletes(list, "").map((x) => x.id)).toEqual(["3", "1", "2"]);
  });
  it("honors limit", () => {
    expect(searchAthletes(list, "", 1)).toHaveLength(1);
  });
});

describe("careerSummary", () => {
  it("aggregates wins / podiums / best rank / years", () => {
    const d: AthleteDetail = {
      id: "x", nm: "王○明", conf: "high", has_uci: false, has_rider: false, teams: ["A隊"], traits: {},
      history: [h({ y: 2023, rank: 1 }), h({ y: 2024, rank: 2 }), h({ y: 2024, rank: 8 })],
    };
    const s = careerSummary(d);
    expect(s.races).toBe(3);
    expect(s.years).toBe(2);
    expect(s.y0).toBe(2023);
    expect(s.y1).toBe(2024);
    expect(s.wins).toBe(1);
    expect(s.podiums).toBe(2);
    expect(s.bestRank).toBe(1);
  });
});

describe("progression", () => {
  it("per-year best percentile + races + best rank, sorted", () => {
    const hist = [
      h({ y: 2024, rank: 10, field: 100 }), // pct 90
      h({ y: 2024, rank: 50, field: 100 }), // pct 50 -> best is 90
      h({ y: 2023, rank: 2, field: 50 }),   // pct 96
    ];
    const p = progression(hist);
    expect(p.map((x) => x.y)).toEqual([2023, 2024]);
    expect(p[0]).toEqual({ y: 2023, pct: 96, races: 1, bestRank: 2 });
    expect(p[1].pct).toBe(90);
    expect(p[1].races).toBe(2);
    expect(p[1].bestRank).toBe(10);
  });
});
