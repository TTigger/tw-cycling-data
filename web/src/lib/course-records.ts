import type { CourseBoard, CourseRecord, CourseRecordsFile } from "./types";

export type GenderFilter = "all" | "M" | "F";

/** Boards for the climb selector, biggest climb (most ascent) first. */
export function boardOptions(file: CourseRecordsFile): CourseBoard[] {
  return Object.values(file).sort((a, b) => b.elev_m - a.elev_m || b.n - a.n);
}

/**
 * Records for one gender, re-ranked 1..N within that gender (so a women's board
 * reads 1,2,3 — not the rider's overall position). "all" keeps the overall rank.
 */
export function genderRecords(board: CourseBoard, g: GenderFilter): CourseRecord[] {
  if (g === "all") return board.records;
  return board.records
    .filter((r) => r.g === g)
    .map((r, i) => ({ ...r, rank: i + 1 }));
}
