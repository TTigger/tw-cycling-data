import { useEffect, useState } from "react";
import { readFavs, type Favs } from "../lib/favorites";
import { raceHref } from "../lib/race-url";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

/** Home "我的最愛" quick-return list, fed from localStorage. Hidden when empty. */
export default function Favorites() {
  const [f, setF] = useState<Favs>({ athletes: [], races: [] });
  useEffect(() => {
    const r = () => setF(readFavs());
    r();
    window.addEventListener("favchange", r);
    return () => window.removeEventListener("favchange", r);
  }, []);

  if (!f.athletes.length && !f.races.length) return null;
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">⭐ 我的最愛</h2>
      <div className="mt-2 flex flex-wrap gap-2">
        {f.athletes.map((a) => (
          <a key={a.id} href={`${base}/athletes?id=${a.id}`}
            className="rounded-lg border border-border bg-bg px-3 py-1.5 text-sm text-ink hover:border-accent">👤 {a.nm}</a>
        ))}
        {f.races.map((r) => (
          <a key={`${r.rk}-${r.y}`} href={raceHref(r.rk, r.y)}
            className="rounded-lg border border-border bg-bg px-3 py-1.5 text-sm text-ink hover:border-accent">🏁 {r.y} {r.rn}</a>
        ))}
      </div>
    </section>
  );
}
