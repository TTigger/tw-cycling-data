export function secondsToHMS(s: number | null): string {
  if (s == null) return "—";
  const sec = Math.round(s);
  const h = Math.floor(sec / 3600);
  const m = Math.floor((sec % 3600) / 60);
  const ss = sec % 60;
  return `${h}:${String(m).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
}

export function hmsToSeconds(t: string): number | null {
  const m = /^(\d{1,2}):(\d{2}):(\d{2})/.exec(t.trim());
  if (!m) return null;
  return +m[1] * 3600 + +m[2] * 60 + +m[3];
}

/** % of finishers you beat (slower than you). `sortedTimes` ascending. */
export function percentileBeaten(mySeconds: number, sortedTimes: number[]): number {
  if (!sortedTimes.length) return 0;
  let slower = 0;
  for (const t of sortedTimes) if (t > mySeconds) slower++;
  return Math.round((slower / sortedTimes.length) * 100);
}
