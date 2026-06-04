export interface SlimRecord {
  rk: string; y: number | null; mon: number | null;
  s: string | null; rc: string | null; cat: string | null;
  g: "M" | "F" | null; ag: string | null;
  t: number | null; rank: number | null;
  dist: number | null; spd: number | null;
  plat: string | null; reg: string | null;
}
export interface RaceIndex {
  rk: string; y: number | null; rn: string; s: string | null;
  rows: number; multi_year: boolean; has_team: boolean; file: string;
}
export interface DetailRow {
  rank: number | null; bib: string | null; name: string | null;
  cat: string | null; g: "M" | "F" | null; ag: string | null;
  team: string | null; t: number | null; label: string | null;
}
