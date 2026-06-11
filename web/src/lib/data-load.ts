import type { SlimRecord, RaceIndex, DetailRow, AthleteIndexEntry, AthleteDetail, ClimbProfile, ClimbVamEntry, Insights, OverseasRaceMeta, OverseasRow } from "./types";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

export async function loadViz(): Promise<SlimRecord[]> {
  const r = await fetch(`${base}/data/viz.json`);
  if (!r.ok) throw new Error(`viz.json ${r.status}`);
  return r.json();
}
export async function loadRaces(): Promise<RaceIndex[]> {
  const r = await fetch(`${base}/data/races.json`);
  if (!r.ok) throw new Error(`races.json ${r.status}`);
  return r.json();
}
export async function loadRaceDetail(file: string): Promise<DetailRow[]> {
  const r = await fetch(`${base}/data/race/${file}.json`);
  if (!r.ok) throw new Error(`race ${file} ${r.status}`);
  return r.json();
}
export async function loadAthletes(): Promise<AthleteIndexEntry[]> {
  const r = await fetch(`${base}/data/athletes.json`);
  if (!r.ok) throw new Error(`athletes.json ${r.status}`);
  return r.json();
}
export async function loadAthlete(id: string): Promise<AthleteDetail> {
  const r = await fetch(`${base}/data/athlete/${id}.json`);
  if (!r.ok) throw new Error(`athlete ${id} ${r.status}`);
  return r.json();
}
export async function loadClimbProfiles(): Promise<ClimbProfile[]> {
  const r = await fetch(`${base}/data/climb_profiles.json`);
  if (!r.ok) throw new Error(`climb_profiles.json ${r.status}`);
  return r.json();
}
export async function loadClimbVam(): Promise<ClimbVamEntry[]> {
  const r = await fetch(`${base}/data/climb_vam.json`);
  if (!r.ok) throw new Error(`climb_vam.json ${r.status}`);
  return r.json();
}
export async function loadInsights(): Promise<Insights> {
  const r = await fetch(`${base}/data/insights.json`);
  if (!r.ok) throw new Error(`insights.json ${r.status}`);
  return r.json();
}
export async function loadOverseasIndex(): Promise<OverseasRaceMeta[]> {
  const r = await fetch(`${base}/data/overseas/index.json`);
  if (!r.ok) throw new Error(`overseas index ${r.status}`);
  return r.json();
}
export async function loadOverseasRace(file: string): Promise<OverseasRow[]> {
  const r = await fetch(`${base}/data/overseas/${file}.json`);
  if (!r.ok) throw new Error(`overseas ${file} ${r.status}`);
  return r.json();
}
