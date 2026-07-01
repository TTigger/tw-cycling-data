import { describe, it, expect } from "vitest";
import { quantile, histogram, boxByGroup, raceSpread, distSpeedPoints, facetOptions, densityRidge } from "./aggregate";

describe("quantile", () => {
  it("odd/even/edges", () => {
    expect(quantile([1, 2, 3, 4, 5], 0.5)).toBe(3);
    expect(quantile([1, 2, 3, 4], 0.5)).toBe(2.5);
    expect(quantile([1, 2, 3, 4, 5], 0)).toBe(1);
    expect(quantile([1, 2, 3, 4, 5], 1)).toBe(5);
    expect(Number.isNaN(quantile([], 0.5))).toBe(true);
  });
});

describe("histogram", () => {
  it("buckets values by bin size", () => {
    const bins = histogram([10, 20, 30, 40], 10);
    expect(bins.length).toBe(4);
    expect(bins[0]).toEqual({ x0: 10, x1: 20, count: 1 });
    expect(bins.every((b) => b.count === 1)).toBe(true);
  });
  it("empty / bad bin -> []", () => {
    expect(histogram([], 10)).toEqual([]);
    expect(histogram([1, 2], 0)).toEqual([]);
  });
});

describe("boxByGroup", () => {
  it("computes 5-number summary per group, drops small groups", () => {
    const rows = [
      ...Array.from({ length: 8 }, (_, i) => ({ ag: "M30", t: (i + 1) * 100 })),
      { ag: "M40", t: 500 },
      { ag: null, t: 999 },
    ];
    const boxes = boxByGroup(rows, 8);
    expect(boxes.length).toBe(1);
    expect(boxes[0].group).toBe("M30");
    expect(boxes[0].n).toBe(8);
    expect(boxes[0].min).toBe(100);
    expect(boxes[0].max).toBe(800);
    expect(boxes[0].median).toBe(450);
  });
});

describe("raceSpread", () => {
  it("excludes 電輔車 race_class", () => {
    const rows = Array.from({ length: 10 }, (_, i) => ({ rk: "E", y: 2025, t: 100 + i, rc: "電輔車", s: "96聯賽" }));
    expect(raceSpread(rows, 10)).toEqual([]);
  });

  it("winner/median/ratio per race; excludes 認證 and small fields", () => {
    const rows = [
      ...Array.from({ length: 10 }, (_, i) => ({ rk: "A", y: 2025, t: 100 + i * 10, rc: "競賽", s: "96聯賽" })),
      { rk: "B", y: 2025, t: 200, rc: "認證", s: null },
      ...Array.from({ length: 10 }, (_, i) => ({ rk: "C", y: 2025, t: 200 + i * 10, rc: "未分類", s: "TBA 長途認證" })),
    ];
    const s = raceSpread(rows, 10);
    expect(s.length).toBe(1);
    expect(s[0].rk).toBe("A");
    expect(s[0].winner).toBe(100);
    expect(s[0].n).toBe(10);
    expect(s[0].ratio).toBeGreaterThan(1);
  });
});

describe("distSpeedPoints", () => {
  it("keeps only rows with both dist and spd", () => {
    const pts = distSpeedPoints([
      { dist: 100, spd: 30, rc: "競賽" },
      { dist: null, spd: 30, rc: "競賽" },
      { dist: 50, spd: null, rc: "市民" },
    ]);
    expect(pts).toEqual([{ dist: 100, spd: 30, rc: "競賽" }]);
  });
});

describe("densityRidge", () => {
  it("returns [binCenter, count] pairs from the histogram (300s bins)", () => {
    // 3 values in bin [0,300) center 150; 2 values in bin [300,600) center 450
    expect(densityRidge([10, 20, 30, 350, 360], 300)).toEqual([[150, 3], [450, 2]]);
  });
  it("empty input -> []", () => {
    expect(densityRidge([], 300)).toEqual([]);
  });
});

describe("facetOptions", () => {
  it("distinct sorted values per facet", () => {
    const rows = [
      { y: 2025, s: "96聯賽", rc: "競賽", g: "M", ag: "M30" },
      { y: 2024, s: "96聯賽", rc: "挑戰", g: "F", ag: null },
    ] as any;
    const f = facetOptions(rows);
    expect(f.years).toEqual([2024, 2025]);
    expect(f.series).toEqual(["96聯賽"]);
    expect(f.raceClasses.sort()).toEqual(["挑戰", "競賽"]);
    expect(f.genders).toEqual(["F", "M"]);
    expect(f.ageGroups).toEqual(["M30"]);
  });
});
