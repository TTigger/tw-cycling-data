export interface JoyLane { base: number; scaled: number[]; }

/** Joy-plot geometry: one lane per band, first band on TOP. The global max pct
 * scales to peak * laneGap so tall peaks slightly overlap the lane above. */
export function joyRidges(pct: number[][], laneGap = 1, peak = 1.6): JoyLane[] {
  const n = pct.length;
  if (!n) return [];
  const maxPct = Math.max(...pct.flat(), 0);
  const scale = maxPct > 0 ? (peak * laneGap) / maxPct : 0;
  return pct.map((row, bi) => ({
    base: (n - 1 - bi) * laneGap,
    scaled: row.map((v) => v * scale),
  }));
}
