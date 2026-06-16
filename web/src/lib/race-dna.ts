import type { RaceDnaAxes, RaceDnaFile } from "./types";

/** The six DNA axes, in radar display order, with their labels and one-line hints. */
export const DNA_AXES = [
  { key: "sel", label: "選擇性", hint: "完賽時間離散度(越高越拉得開)" },
  { key: "size", label: "規模", hint: "完賽人數" },
  { key: "climb", label: "爬坡度", hint: "由均速反推(越慢越偏爬坡)" },
  { key: "prest", label: "含金量", hint: "常客(出賽多屆者)比例" },
  { key: "repeat", label: "回頭率", hint: "跨屆重複參賽比例" },
  { key: "women", label: "女子比例", hint: "完賽者女性占比" },
] as const;

export type DnaAxisKey = (typeof DNA_AXES)[number]["key"];

/** DNA axes for one race-year, or null if that edition wasn't fingerprinted. */
export function dnaFor(
  file: RaceDnaFile, rk: string, year: number | string | null,
): RaceDnaAxes | null {
  if (year == null) return null;
  return file[rk]?.years[String(year)] ?? null;
}

/** Axis values in DNA_AXES order — ready to feed an ECharts radar series. */
export function dnaRadarValues(axes: RaceDnaAxes): number[] {
  return DNA_AXES.map((a) => axes[a.key]);
}

export interface DnaRaceOption { rk: string; year: string; name: string; label: string; }

/** Flat, name-sorted list of every fingerprinted race-year (for a compare picker). */
export function dnaRaceList(file: RaceDnaFile): DnaRaceOption[] {
  const out: DnaRaceOption[] = [];
  for (const [rk, info] of Object.entries(file)) {
    const name = info.name ?? rk;
    for (const year of Object.keys(info.years)) {
      out.push({ rk, year, name, label: `${year} ${name}` });
    }
  }
  return out.sort((a, b) => a.name.localeCompare(b.name) || b.year.localeCompare(a.year));
}
