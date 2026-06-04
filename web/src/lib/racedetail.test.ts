import { describe, it, expect } from "vitest";
import { categoriesOf, podium, largestCategory, categoryPodium, teamStrength, crossYear } from "./racedetail";
import type { DetailRow } from "./types";

function d(p: Partial<DetailRow>): DetailRow {
  return { rank: 1, bib: "1", name: "甲", cat: "菁英", g: "M", ag: null, team: "A隊", t: 1000, label: null, ...p };
}

describe("categoriesOf", () => {
  it("distinct sorted non-null categories", () => {
    expect(categoriesOf([d({ cat: "B" }), d({ cat: "A" }), d({ cat: "A" }), d({ cat: null })])).toEqual(["A", "B"]);
  });
});

describe("podium", () => {
  it("top 3 by rank", () => {
    const p = podium([d({ rank: 3, name: "丙" }), d({ rank: 1, name: "甲" }), d({ rank: 2, name: "乙" }), d({ rank: 4, name: "丁" })]);
    expect(p.map((x) => x.name)).toEqual(["甲", "乙", "丙"]);
  });
});

describe("largestCategory", () => {
  it("returns the category with the most rows (ignoring null)", () => {
    const rows = [d({ cat: "A" }), d({ cat: "B" }), d({ cat: "B" }), d({ cat: null })];
    expect(largestCategory(rows)).toBe("B");
  });
});

describe("categoryPodium", () => {
  it("top-3 of a category by time, positioned 1-2-3", () => {
    const rows = [
      d({ cat: "M25", t: 1200, name: "丙" }), d({ cat: "M25", t: 1000, name: "甲" }),
      d({ cat: "M25", t: 1100, name: "乙" }), d({ cat: "M25", t: 1300, name: "丁" }),
      d({ cat: "其他", t: 500, name: "別組" }),
    ];
    const p = categoryPodium(rows, "M25", 3);
    expect(p.map((e) => e.name)).toEqual(["甲", "乙", "丙"]);
    expect(p.map((e) => e.rank)).toEqual([1, 2, 3]);
  });
});

describe("teamStrength", () => {
  it("counts top-cutoff and podium per team, sorted", () => {
    const rows = [
      d({ team: "A隊", rank: 1 }), d({ team: "A隊", rank: 2 }), d({ team: "A隊", rank: 12 }),
      d({ team: "B隊", rank: 5 }), d({ team: null, rank: 1 }),
    ];
    const ts = teamStrength(rows, 10, 10);
    expect(ts[0].team).toBe("A隊");
    expect(ts[0].top).toBe(2);
    expect(ts[0].podium).toBe(2);
    expect(ts.find((t) => t.team === "B隊")?.top).toBe(1);
  });
});

describe("crossYear", () => {
  it("winner(min)/median/n per year, sorted by year", () => {
    const rows = [
      { y: 2025, t: 100 }, { y: 2025, t: 200 }, { y: 2025, t: 300 },
      { y: 2024, t: 400 }, { y: 2024, t: 600 },
    ];
    const cy = crossYear(rows);
    expect(cy.map((x) => x.y)).toEqual([2024, 2025]);
    expect(cy[0]).toEqual({ y: 2024, winner: 400, median: 500, n: 2 });
    expect(cy[1].winner).toBe(100);
    expect(cy[1].median).toBe(200);
  });
});
