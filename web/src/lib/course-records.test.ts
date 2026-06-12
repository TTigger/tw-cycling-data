import { describe, it, expect } from "vitest";
import { boardOptions, genderRecords } from "./course-records";
import type { CourseBoard, CourseRecordsFile } from "./types";

function rec(p: Partial<CourseBoard["records"][number]>) {
  return { rank: 1, nm: "x", t: 6000, vam: 1800, wkg: 4.2, y: 2024, g: "M" as const,
    cat: null, id: "a", link: true, ...p };
}
const board: CourseBoard = {
  name: "武嶺", rk: "wuling", dist_km: 50, elev_m: 3000, grade: 6, n: 3,
  records: [
    rec({ rank: 1, t: 6000, g: "M" }),
    rec({ rank: 2, t: 6500, g: "F" }),
    rec({ rank: 3, t: 7000, g: "M" }),
  ],
};
const file: CourseRecordsFile = {
  wuling: board,
  small: { ...board, rk: "small", name: "小山", elev_m: 800, n: 1, records: [rec({})] },
};

describe("boardOptions", () => {
  it("orders boards by elevation, biggest first", () => {
    expect(boardOptions(file).map((b) => b.rk)).toEqual(["wuling", "small"]);
  });
});

describe("genderRecords", () => {
  it("keeps overall ranks for 'all'", () => {
    expect(genderRecords(board, "all").map((r) => r.rank)).toEqual([1, 2, 3]);
  });
  it("filters to one gender and re-ranks 1..N", () => {
    const men = genderRecords(board, "M");
    expect(men.length).toBe(2);
    expect(men.map((r) => r.rank)).toEqual([1, 2]);     // re-ranked within men
    expect(men.map((r) => r.t)).toEqual([6000, 7000]);  // the two men, in time order
  });
});
