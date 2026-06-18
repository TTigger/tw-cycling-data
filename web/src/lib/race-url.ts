const base = import.meta.env.BASE_URL.replace(/\/$/, "");

/** Slug for a race's pre-rendered SSG page (`/race/<slug>`). Must match
 * scrapers/build_viz.race_file_name exactly — validated to reproduce all of
 * races.json's `file` values. */
export function raceSlug(rk: string, y: number | string | null): string {
  const safe = rk.replace(/[^0-9A-Za-z一-鿿]+/g, "-").replace(/^-+|-+$/g, "");
  return `${safe}__${y}`;
}

/** Href to the crawlable SSG race page (has per-race title/description/OG), the
 * preferred internal link over the query-param SPA (`/race?rk=&y=`). */
export function raceHref(rk: string, y: number | string | null): string {
  return `${base}/race/${encodeURIComponent(raceSlug(rk, y))}`;
}
