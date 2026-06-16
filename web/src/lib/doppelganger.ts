import type { AthleteFeature } from "./types";

// Axis weights for the fingerprint [climb, flat, tt, overall, age]. Overall
// strength dominates; age is a soft tiebreaker; tt is down-weighted (sparser,
// noisier signal). Tuned by hand, not learned — adjust here if matches feel off.
export const DOPPEL_WEIGHTS = [1, 1, 0.8, 1.3, 0.5];
// Distance → similarity-% decay. Picked so a typical close neighbor reads ~85-95%
// and a distant one trails off, keeping the score human-readable, not a raw metric.
const SIM_SCALE = 2.5;

export interface Doppel {
  id: string;
  dist: number;
  sim: number;
}

/** Weighted Euclidean distance between two standardized fingerprint vectors. */
export function fingerprintDistance(a: number[], b: number[]): number {
  let s = 0;
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) {
    const d = a[i] - b[i];
    s += (DOPPEL_WEIGHTS[i] ?? 1) * d * d;
  }
  return Math.sqrt(s);
}

/** Map a distance to a 0–100 similarity score (monotonically decreasing). */
export function similarity(dist: number): number {
  return Math.round(100 * Math.exp(-dist / SIM_SCALE));
}

/**
 * The `k` riders most similar to `targetId`. Same gender only (fingerprints are
 * standardized within gender, so cross-gender distances aren't comparable), and
 * the target itself is excluded. Empty if the target isn't in the feature pool
 * (e.g. unknown gender or too few results).
 */
export function doppelgangers(
  feats: AthleteFeature[], targetId: string, k = 6,
): Doppel[] {
  const target = feats.find((f) => f.id === targetId);
  if (!target) return [];
  const out: Doppel[] = [];
  for (const f of feats) {
    if (f.id === targetId || f.g !== target.g) continue;
    const dist = fingerprintDistance(target.v, f.v);
    out.push({ id: f.id, dist, sim: similarity(dist) });
  }
  out.sort((a, b) => a.dist - b.dist);
  return out.slice(0, k);
}

/** Short style label from a fingerprint: climb-vs-flat lean. */
export function fingerprintLean(v: number[]): string {
  const diff = (v[0] ?? 0) - (v[1] ?? 0);
  if (diff > 0.5) return "偏爬坡";
  if (diff < -0.5) return "偏平路";
  return "全能";
}
