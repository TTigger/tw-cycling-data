import { describe, it, expect } from "vitest";
import { categoriesOf, largestCategory, categoryPodium, teamStrength, crossYear, rerankByTime, comparableGroups, distinctLabels, largestComparableGroup } from "./racedetail";
import type { DetailRow } from "./types";

function d(p: Partial<DetailRow>): DetailRow {
  return { rank: 1, bib: "1", name: "甲", cat: "菁英", g: "M", ag: null, team: "A隊", t: 1000, label: null, ...p };
}

describe("categoriesOf", () => {
  it("distinct sorted non-null categories", () => {
    expect(categoriesOf([d({ cat: "B" }), d({ cat: "A" }), d({ cat: "A" }), d({ cat: null })])).toEqual(["A", "B"]);
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

describe("rerankByTime", () => {
  it("places by finish time ascending, 1..N", () => {
    const rows = [d({ name: "丙", t: 1200 }), d({ name: "甲", t: 1000 }), d({ name: "乙", t: 1100 })];
    const r = rerankByTime(rows);
    expect(r.map((x) => x.name)).toEqual(["甲", "乙", "丙"]);
    expect(r.map((x) => x.place)).toEqual([1, 2, 3]);
  });
  it("rows without time go last with null place; preserves source rank", () => {
    const rows = [d({ name: "甲", t: 1000, rank: 5 }), d({ name: "無", t: null, rank: 9 })];
    const r = rerankByTime(rows);
    expect(r.map((x) => x.name)).toEqual(["甲", "無"]);
    expect(r.map((x) => x.place)).toEqual([1, null]);
    expect(r.map((x) => x.rank)).toEqual([5, 9]);
  });
});

describe("comparableGroups", () => {
  it("splits one cat with multiple labels into cat·label groups", () => {
    const rows = [
      d({ cat: "男子菁英", label: "155公里公路賽", t: 16000 }),
      d({ cat: "男子菁英", label: "20公里計時賽", t: 1500 }),
      d({ cat: "男子菁英", label: "155公里公路賽", t: 16100 }),
    ];
    const g = comparableGroups(rows);
    expect(g.map((x) => x.name).sort()).toEqual(
      ["男子菁英 · 155公里公路賽", "男子菁英 · 20公里計時賽"].sort(),
    );
    expect(g.find((x) => x.label === "155公里公路賽")?.count).toBe(2);
  });
  it("single-label cat shows just the cat name", () => {
    const rows = [d({ cat: "107K挑戰", label: "107K挑戰" }), d({ cat: "107K挑戰", label: "107K挑戰" })];
    expect(comparableGroups(rows).map((x) => x.name)).toEqual(["107K挑戰"]);
  });
  it("empty cat falls back to label, then 未分組", () => {
    expect(comparableGroups([d({ cat: null, label: "X" })])[0].name).toBe("X");
    expect(comparableGroups([d({ cat: null, label: null })])[0].name).toBe("未分組");
  });
  it("groups sorted by count descending", () => {
    const rows = [d({ cat: "A", label: null }), d({ cat: "B", label: null }), d({ cat: "B", label: null })];
    expect(comparableGroups(rows).map((x) => x.cat)).toEqual(["B", "A"]);
  });
});

describe("distinctLabels", () => {
  it("counts distinct non-empty labels", () => {
    expect(distinctLabels([d({ label: "a" }), d({ label: "a" }), d({ label: "b" }), d({ label: null })])).toBe(2);
  });
});

describe("largestComparableGroup", () => {
  it("returns the group with the most rows", () => {
    const rows = [d({ cat: "A", label: null }), d({ cat: "B", label: null }), d({ cat: "B", label: null })];
    expect(largestComparableGroup(rows)?.cat).toBe("B");
  });
});
