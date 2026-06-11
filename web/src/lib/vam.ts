export const VAM_MIN = 100;
export const VAM_MAX = 3000;

/** Vertical ascent metres per hour = elev / (seconds/3600). null if invalid. */
export function vam(elevM: number, seconds: number | null): number | null {
  if (!elevM || !seconds || seconds <= 0) return null;
  return Math.round(elevM / (seconds / 3600));
}

/** Ferrari relative-power estimate (rough): vam / (100 * (2 + grade%/10)). */
export function wkgEstimate(vamValue: number | null, gradePct: number): number | null {
  if (vamValue == null || !gradePct) return null;
  return Math.round((vamValue / (100 * (2 + gradePct / 10))) * 10) / 10;
}

/** Reject timing-error / DNF outliers. */
export function isPlausibleVam(v: number | null): boolean {
  return v != null && v >= VAM_MIN && v <= VAM_MAX;
}
