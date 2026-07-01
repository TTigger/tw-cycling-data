import type { SlimRecord, RaceIndex, DetailRow, AthleteIndexEntry, AthleteDetail, AthleteFeature, ClimbProfile, ClimbVamEntry, Insights, OverseasRaceMeta, OverseasRow, Coverage, CourseRecordsFile, RaceDifficultyFile, RaceDnaFile, SeriesFile, TeamIndexEntry, TeamDetail } from "./types";
import type { OverviewData, CrossYearMap } from "./overview";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");
// Versioned public API namespace. All reads go through /data/v1/.
const API = `${base}/data/v1`;

export async function loadViz(): Promise<SlimRecord[]> {
  const r = await fetch(`${API}/viz.json`);
  if (!r.ok) throw new Error(`viz.json ${r.status}`);
  return r.json();
}
export async function loadRaces(): Promise<RaceIndex[]> {
  const r = await fetch(`${API}/races.json`);
  if (!r.ok) throw new Error(`races.json ${r.status}`);
  return r.json();
}
export async function loadOverview(): Promise<OverviewData> {
  const r = await fetch(`${API}/overview.json`);
  if (!r.ok) throw new Error(`overview.json ${r.status}`);
  return r.json();
}
let _crossYearCache: Promise<CrossYearMap> | null = null;
/** Per-race cross-year winner/median map. Cached per page session. */
export async function loadCrossYear(): Promise<CrossYearMap> {
  if (!_crossYearCache) {
    _crossYearCache = fetch(`${API}/race_crossyear.json`).then((r) => {
      if (!r.ok) throw new Error(`race_crossyear.json ${r.status}`);
      return r.json();
    });
  }
  return _crossYearCache;
}
export async function loadRaceDetail(file: string): Promise<DetailRow[]> {
  const r = await fetch(`${API}/race/${file}.json`);
  if (!r.ok) throw new Error(`race ${file} ${r.status}`);
  return r.json();
}
export async function loadAthletes(): Promise<AthleteIndexEntry[]> {
  const r = await fetch(`${API}/athletes.json`);
  if (!r.ok) throw new Error(`athletes.json ${r.status}`);
  return r.json();
}
export async function loadAthlete(id: string): Promise<AthleteDetail> {
  const r = await fetch(`${API}/athlete/${id}.json`);
  if (!r.ok) throw new Error(`athlete ${id} ${r.status}`);
  return r.json();
}
let _featuresCache: Promise<AthleteFeature[]> | null = null;
/** All riders' fingerprint vectors (for the doppelganger search). Cached: one
 * fetch per page session, reused across profile views. */
export async function loadAthleteFeatures(): Promise<AthleteFeature[]> {
  if (!_featuresCache) {
    _featuresCache = fetch(`${API}/athlete_features.json`).then((r) => {
      if (!r.ok) throw new Error(`athlete_features.json ${r.status}`);
      return r.json();
    });
  }
  return _featuresCache;
}
let _difficultyCache: Promise<RaceDifficultyFile> | null = null;
/** Cross-year race difficulty coefficients. Cached per page session. */
export async function loadRaceDifficulty(): Promise<RaceDifficultyFile> {
  if (!_difficultyCache) {
    _difficultyCache = fetch(`${API}/race_difficulty.json`).then((r) => {
      if (!r.ok) throw new Error(`race_difficulty.json ${r.status}`);
      return r.json();
    });
  }
  return _difficultyCache;
}
let _dnaCache: Promise<RaceDnaFile> | null = null;
/** Per-race DNA fingerprints (6 normalized axes). Cached per page session. */
export async function loadRaceDna(): Promise<RaceDnaFile> {
  if (!_dnaCache) {
    _dnaCache = fetch(`${API}/race_dna.json`).then((r) => {
      if (!r.ok) throw new Error(`race_dna.json ${r.status}`);
      return r.json();
    });
  }
  return _dnaCache;
}
export async function loadSeries(): Promise<SeriesFile> {
  const r = await fetch(`${API}/series.json`);
  if (!r.ok) throw new Error(`series.json ${r.status}`);
  return r.json();
}
export async function loadTeams(): Promise<TeamIndexEntry[]> {
  const r = await fetch(`${API}/teams.json`);
  if (!r.ok) throw new Error(`teams.json ${r.status}`);
  return r.json();
}
export async function loadTeam(id: string): Promise<TeamDetail> {
  const r = await fetch(`${API}/team/${id}.json`);
  if (!r.ok) throw new Error(`team ${id} ${r.status}`);
  return r.json();
}
export async function loadClimbProfiles(): Promise<ClimbProfile[]> {
  const r = await fetch(`${API}/climb_profiles.json`);
  if (!r.ok) throw new Error(`climb_profiles.json ${r.status}`);
  return r.json();
}
export async function loadClimbVam(): Promise<ClimbVamEntry[]> {
  const r = await fetch(`${API}/climb_vam.json`);
  if (!r.ok) throw new Error(`climb_vam.json ${r.status}`);
  return r.json();
}
export async function loadCourseRecords(): Promise<CourseRecordsFile> {
  const r = await fetch(`${API}/course_records.json`);
  if (!r.ok) throw new Error(`course_records.json ${r.status}`);
  return r.json();
}
export async function loadInsights(): Promise<Insights> {
  const r = await fetch(`${API}/insights.json`);
  if (!r.ok) throw new Error(`insights.json ${r.status}`);
  return r.json();
}
export async function loadOverseasIndex(): Promise<OverseasRaceMeta[]> {
  const r = await fetch(`${API}/overseas/index.json`);
  if (!r.ok) throw new Error(`overseas index ${r.status}`);
  return r.json();
}
export async function loadOverseasRace(file: string): Promise<OverseasRow[]> {
  const r = await fetch(`${API}/overseas/${file}.json`);
  if (!r.ok) throw new Error(`overseas ${file} ${r.status}`);
  return r.json();
}
export async function loadCoverage(): Promise<Coverage> {
  const r = await fetch(`${API}/coverage.json`);
  if (!r.ok) throw new Error(`coverage.json ${r.status}`);
  return r.json();
}
export async function loadBenchmarks(): Promise<import("./types").BenchmarkFile> {
  const r = await fetch(`${API}/benchmarks.json`);
  if (!r.ok) throw new Error(`benchmarks.json ${r.status}`);
  return r.json();
}
export async function loadManifest(): Promise<import("./types").Manifest> {
  const r = await fetch(`${API}/manifest.json`);
  if (!r.ok) throw new Error(`manifest.json ${r.status}`);
  return r.json();
}
export interface HomeRidgeline { unit: string; nodes: { label: string; x: number; y: number; median: number; finishers: number }[]; }
export async function loadHomeRidgeline(): Promise<HomeRidgeline> {
  const r = await fetch(`${API}/home_ridgeline.json`);
  if (!r.ok) throw new Error(`home_ridgeline.json ${r.status}`);
  return r.json();
}
export async function fetchEndpoint(path: string): Promise<unknown> {
  const r = await fetch(`${API}/${path}`);
  if (!r.ok) throw new Error(`${path} ${r.status}`);
  return r.json();
}
