export interface SlimRecord {
  rk: string; y: number | null; mon: number | null;
  s: string | null; rc: string | null; cat: string | null;
  g: "M" | "F" | null; ag: string | null;
  t: number | null; rank: number | null;
  dist: number | null; spd: number | null;
  plat: string | null; reg: string | null;
}
export interface Completion {
  fin: number; total: number; rate: number; counts: Record<string, number>;
}
export interface RaceIndex {
  rk: string; y: number | null; rn: string; s: string | null;
  rows: number; multi_year: boolean; has_team: boolean; file: string;
  completion?: Completion;
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
  tm?: string | null;  // most-recent representative team, for search disambiguation
}
export interface AthleteHistoryRow {
  y: number | null; rk: string; rn: string; cat: string | null;
  g: "M" | "F" | null; ag: string | null; team: string | null;
  rank: number | null; t: number | null; label: string | null;
  d: string | null; field: number | null;
}
export interface AthleteFeature { id: string; g: "M" | "F"; v: number[]; }
export interface AthleteTrait { pct: number; n: number; }
export interface RivalEntry { id: string; nm: string; w: number; l: number; meets: number; }
export interface AthleteDetail {
  id: string; nm: string; conf: Confidence; has_uci: boolean; has_rider: boolean;
  teams: string[]; traits: Record<string, AthleteTrait>;
  rivals?: RivalEntry[]; history: AthleteHistoryRow[];
}
export interface SeriesStation { rk: string; name: string | null; n: number | null; }
export interface SeriesStandingRow {
  id: string; nm: string; pts: number; n: number; best: number; link: boolean;
}
export interface SeriesSeason { stations: SeriesStation[]; standings: SeriesStandingRow[]; }
export interface SeriesInfo { name: string; seasons: Record<string, SeriesSeason>; }
export type SeriesFile = Record<string, SeriesInfo>;

export interface YearDifficulty { median: number; coeff: number; n: number; }
export interface RaceDifficulty {
  name: string | null; baseline: number; years: Record<string, YearDifficulty>;
}
export type RaceDifficultyFile = Record<string, RaceDifficulty>;

export interface RaceDnaAxes {
  n: number; sel: number; size: number; climb: number;
  prest: number; repeat: number; women: number;
}
export interface RaceDnaInfo { name: string | null; years: Record<string, RaceDnaAxes>; }
export type RaceDnaFile = Record<string, RaceDnaInfo>;

export interface ClimbProfile {
  race_key: string; name: string;
  dist_km: number; elev_m: number; grade: number;  // grade = elev_m/(dist_km*1000)*100
  conf: "high" | "est"; src: string;
}
export interface ClimbVamEntry {
  id: string; nm: string; best_vam: number; best_wkg: number | null;
  climb: string; y: number | null; conf: "high" | "est"; g: "M" | "F" | null;
}
export interface CourseRecord {
  rank: number; nm: string; t: number; vam: number; wkg: number | null;
  y: number | null; g: "M" | "F" | null; cat: string | null;
  id: string | null; link: boolean;
}
export interface CourseBoard {
  name: string; rk: string; dist_km: number; elev_m: number; grade: number;
  n: number; records: CourseRecord[];
}
export type CourseRecordsFile = Record<string, CourseBoard>;

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
export interface GeoRegion { region: string; races: number; rows: number; }

export interface OverseasRaceMeta {
  file: string; race: string; region: string; date: string; source: string; n: number;
}
export interface OverseasRow {
  category_raw: string | null; gender: "M" | "F" | null; rank_overall: number | null;
  bib: string | null; name_masked: string | null; team: string | null;
  finish_time: string | null; finish_seconds: number | null;
}

export interface TeamIndexEntry {
  id: string; name: string; riders: number; races: number;
  wins: number; podiums: number; y0: number | null; y1: number | null;
}
export interface TeamRosterRider {
  id: string; nm: string; link: boolean; n: number;
  best: number | null; y0: number | null; y1: number | null;
}
export interface TeamHighlight {
  id: string; nm: string; rn: string | null; rk: string | null;
  y: number | null; rank: number | null; pct: number;
}
export interface TeamDetail extends TeamIndexEntry {
  rows: number; best: number | null;
  byYear: { y: number; riders: number; races: number }[];
  roster: TeamRosterRider[];
  highlights: TeamHighlight[];
}

export interface CoverageGap { race: string; calendar: string; guess_source: string; }
export interface Coverage {
  summary: {
    rows: number; races: number; by_source: Record<string, number>;
    y0: number; y1: number; overseas: number; calendars: string[];
  };
  gaps: CoverageGap[];
}
export interface RecordAthlete { id: string; nm: string; g: "M" | "F" | null; v: number; }
export interface RecordRace { rk: string; name: string; y: number; n: number; }
export interface RecordLoyal { id: string; nm: string; rk: string; name: string; v: number; }
export interface Records {
  biggest_field: RecordRace[];
  most_starts: RecordAthlete[];
  most_wins: RecordAthlete[];
  most_races: RecordAthlete[];
  longest_streak: RecordAthlete[];
  most_loyal: RecordLoyal[];
}
export interface Insights {
  age_curve: AgeCurvePoint[];
  breakout: BreakoutEntry[];
  ratings: RaceRating[];
  geo: GeoRegion[];
  records: Records;
}

export interface Cohort { n: number; type: "all" | "age" | "cat"; label: string; bp: number[]; }
export interface BenchmarkRace { rn: string; years: number[]; cohorts: Record<string, Cohort>; }
export type BenchmarkFile = Record<string, BenchmarkRace>;

export interface ManifestEndpoint { path: string; kind: string; description: string; }
export interface ManifestStats {
  records: number; races: number; race_editions: number; series: number;
  athletes: number; teams: number; sources: number; year_min: number; year_max: number;
}
export interface Manifest {
  api_version: string; dataset: string; homepage: string; license: string;
  attribution: string; stats: ManifestStats; endpoints: ManifestEndpoint[];
}
