import { describe, it, expect } from "vitest";
import { kpiStats, monthYearHeat, trendByYearSeries, womenShareBySeries, compositionByClass } from "./overview";
import type { SlimRecord } from "./types";

function rec(p: Partial<SlimRecord>): SlimRecord {
  return { rk: "r", y: 2025, mon: 1, s: "S", rc: "競賽", cat: null, g: null, ag: null,
    t: 1000, rank: 1, dist: null, spd: null, plat: "x", reg: null, ...p };
}

describe("kpiStats", () => {
  it("counts records, distinct races (rk), series, year range", () => {
    const k = kpiStats([
      rec({ rk: "a", s: "S1", y: 2024 }), rec({ rk: "a", s: "S1", y: 2025 }),
      rec({ rk: "b", s: "S2", y: 2025 }),
    ]);
    expect(k.records).toBe(3);
    expect(k.races).toBe(2);
    expect(k.series).toBe(2);
    expect(k.minYear).toBe(2024);
    expect(k.maxYear).toBe(2025);
  });
});

describe("monthYearHeat", () => {
  it("counts 人次 per (month, year) and exposes years + max", () => {
    const h = monthYearHeat([
      rec({ mon: 9, y: 2025 }), rec({ mon: 9, y: 2025 }), rec({ mon: 3, y: 2024 }),
    ]);
    expect(h.years).toEqual([2024, 2025]);
    expect(h.max).toBe(2);
    expect(h.cells).toContainEqual([8, 1, 2]);
    expect(h.cells).toContainEqual([2, 0, 1]);
  });
});

describe("trendByYearSeries", () => {
  it("stacks counts per year by top series", () => {
    const t = trendByYearSeries([
      rec({ y: 2024, s: "A" }), rec({ y: 2025, s: "A" }), rec({ y: 2025, s: "B" }),
    ], 8);
    expect(t.years).toEqual([2024, 2025]);
    expect(t.series.sort()).toEqual(["A", "B"]);
    expect(t.counts["A"]).toEqual([1, 1]);
    expect(t.counts["B"]).toEqual([0, 1]);
  });

  it("buckets series beyond topN into 其他", () => {
    const rows = [
      rec({ y: 2025, s: "A" }), rec({ y: 2025, s: "A" }), // A total 2
      rec({ y: 2025, s: "B" }),                            // B total 1
      rec({ y: 2025, s: "C" }),                            // C total 1
    ];
    const t = trendByYearSeries(rows, 1); // only top-1 (A) named, B+C -> 其他
    expect(t.series).toContain("A");
    expect(t.series).toContain("其他");
    expect(t.counts["A"]).toEqual([2]);
    expect(t.counts["其他"]).toEqual([2]); // B + C
  });
});

describe("womenShareBySeries", () => {
  it("female share per series above minN, sorted by total desc", () => {
    const rows = [
      ...Array.from({ length: 3 }, () => rec({ s: "X", g: "F" })),
      ...Array.from({ length: 7 }, () => rec({ s: "X", g: "M" })),
      rec({ s: "Y", g: "F" }),
    ];
    const w = womenShareBySeries(rows, 2);
    expect(w.length).toBe(1);
    expect(w[0].series).toBe("X");
    expect(w[0].f).toBe(3);
    expect(w[0].total).toBe(10);
    expect(w[0].pct).toBe(30);
  });
});

describe("compositionByClass", () => {
  it("counts M/F/unknown per race_class, sorted by total desc", () => {
    const c = compositionByClass([
      rec({ rc: "競賽", g: "M" }), rec({ rc: "競賽", g: "F" }), rec({ rc: "挑戰", g: null }),
    ]);
    expect(c.classes[0]).toBe("競賽");
    expect(c.male[0]).toBe(1);
    expect(c.female[0]).toBe(1);
    expect(c.unknown[c.classes.indexOf("挑戰")]).toBe(1);
  });
});
