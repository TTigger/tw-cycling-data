import type { SeriesFile } from "./types";

export interface SeriesOption {
  key: string; name: string; seasons: string[]; stations: number;
}

/**
 * Series for the picker: each with its seasons (newest first) and total station
 * count across seasons. Sorted by total stations (the most "complete" series
 * first), then name.
 */
export function seriesList(file: SeriesFile): SeriesOption[] {
  return Object.entries(file)
    .map(([key, info]) => ({
      key,
      name: info.name,
      seasons: Object.keys(info.seasons).sort((a, b) => b.localeCompare(a)),
      stations: Object.values(info.seasons).reduce((s, se) => s + se.stations.length, 0),
    }))
    .sort((a, b) => b.stations - a.stations || a.name.localeCompare(b.name));
}
