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

export type Confidence = "high" | "med" | "low";

export interface AthleteIndexEntry {
  id: string; nm: string; n: number; ny: number; nr: number;
  y0: number | null; y1: number | null; best: number | null;
  conf: Confidence; uci: boolean; rid: boolean;
}
export interface AthleteHistoryRow {
  y: number | null; rk: string; rn: string; cat: string | null;
  g: "M" | "F" | null; ag: string | null; team: string | null;
  rank: number | null; t: number | null; label: string | null;
  d: string | null; field: number | null;
}
export interface AthleteDetail {
  id: string; nm: string; conf: Confidence; has_uci: boolean; has_rider: boolean;
  teams: string[]; history: AthleteHistoryRow[];
}
