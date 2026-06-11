import type { SlimRecord, RaceIndex, DetailRow, AthleteIndexEntry, AthleteDetail } from "./types";

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
