import type { RaceIndex } from "./types";

const CLIMB_RE = /武嶺|KOM|登山王|塔塔加|大禹嶺|爬坡/i;

export function isClimbRace(rn: string | null): boolean {
  return !!rn && CLIMB_RE.test(rn);
}

export function climbRaces(races: RaceIndex[]): RaceIndex[] {
  return races
    .filter((r) => isClimbRace(r.rn))
    .sort((a, b) => (b.y ?? 0) - (a.y ?? 0) || b.rows - a.rows);
}
