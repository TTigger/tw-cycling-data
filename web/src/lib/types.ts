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
export interface AthleteTrait { pct: number; n: number; }
export interface RivalEntry { id: string; nm: string; w: number; l: number; meets: number; }
export interface AthleteDetail {
  id: string; nm: string; conf: Confidence; has_uci: boolean; has_rider: boolean;
  teams: string[]; traits: Record<string, AthleteTrait>;
  rivals?: RivalEntry[]; history: AthleteHistoryRow[];
}
export interface ClimbProfile {
  race_key: string; name: string;
  dist_km: number; elev_m: number; grade: number;  // grade = elev_m/(dist_km*1000)*100
  conf: "high" | "est"; src: string;
}
export interface ClimbVamEntry {
  id: string; nm: string; best_vam: number; best_wkg: number | null;
  climb: string; y: number | null; conf: "high" | "est"; g: "M" | "F" | null;
}

export interface AgeCurvePoint {
  band: string; g: "M" | "F" | "all"; n: number; p25: number; p50: number; p75: number;
}
export interface BreakoutEntry {
  id: string; nm: string; g: "M" | "F" | null; anchored: boolean;
  from_y: number; to_y: number; from_pct: number; to_pct: number; jump: number;
}
export interface RaceRating {
  race_key: string; name: string; score: number; stars: number;
  med_field: number; editions: number; regular_pct: number; years: number[];
}
export interface Insights {
  age_curve: AgeCurvePoint[];
  breakout: BreakoutEntry[];
  ratings: RaceRating[];
}
