// Client-only favorites, persisted to localStorage (no backend). Pure list
// logic (toggleBy) is unit-tested; the localStorage wrappers are thin glue.
export interface FavAthlete { id: string; nm: string; }
export interface FavRace { rk: string; y: number; rn: string; }
export interface Favs { athletes: FavAthlete[]; races: FavRace[]; }

const KEY = "twcd-favorites";

/** Toggle an item in a list keyed by `key` (newest first); returns a new list. */
export function toggleBy<T>(list: T[], item: T, key: (t: T) => string): T[] {
  const k = key(item);
  return list.some((x) => key(x) === k) ? list.filter((x) => key(x) !== k) : [item, ...list];
}

const raceKey = (r: { rk: string; y: number }) => `${r.rk}__${r.y}`;

export function readFavs(): Favs {
  try {
    const v = JSON.parse(localStorage.getItem(KEY) || "{}");
    return { athletes: Array.isArray(v.athletes) ? v.athletes : [], races: Array.isArray(v.races) ? v.races : [] };
  } catch { return { athletes: [], races: [] }; }
}

function write(f: Favs) {
  try {
    localStorage.setItem(KEY, JSON.stringify(f));
    window.dispatchEvent(new Event("favchange"));
  } catch { /* private mode / quota — ignore */ }
}

export function isFavAthlete(id: string): boolean {
  return readFavs().athletes.some((a) => a.id === id);
}
export function toggleFavAthlete(a: FavAthlete): void {
  const f = readFavs();
  write({ ...f, athletes: toggleBy(f.athletes, a, (x) => x.id) });
}
export function isFavRace(rk: string, y: number): boolean {
  return readFavs().races.some((r) => raceKey(r) === raceKey({ rk, y }));
}
export function toggleFavRace(r: FavRace): void {
  const f = readFavs();
  write({ ...f, races: toggleBy(f.races, r, raceKey) });
}
