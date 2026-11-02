import { useEffect, useState } from "react";
import { loadManifest } from "../../lib/data-load";
import type { ManifestStats } from "../../lib/types";
import { OPEN_SEARCH } from "../CommandPalette";

/** Compact home intro: what the site is, one line of scale, and the search box
 * (the most common reason to visit is looking up a rider or a race). */
export default function HomeHero() {
  const [stats, setStats] = useState<ManifestStats | null>(null);
  useEffect(() => {
    loadManifest().then((m) => setStats(m.stats)).catch(() => setStats(null));
  }, []);
  const fmt = (n: number) => n.toLocaleString("en-US");
  return (
    <section className="grid gap-5 pt-4 sm:pt-8">
      <div>
        <p className="eyebrow">TAIWAN ROAD CYCLING · 完賽數據</p>
        <h1 className="mt-2 font-display text-4xl font-semibold leading-tight tracking-tight text-ink sm:text-5xl">
          台灣公路賽事成績
        </h1>
        <p className="mt-2 min-h-[1.5rem] font-mono text-sm tabular-nums text-muted">
          {stats && <>{stats.year_min}–{stats.year_max} · {fmt(stats.records)} 筆完賽 · {fmt(stats.races)} 場賽事 · {stats.sources} 個來源</>}
        </p>
      </div>
      <button type="button" onClick={() => window.dispatchEvent(new Event(OPEN_SEARCH))}
        className="flex w-full max-w-2xl items-center justify-between gap-3 rounded-xl border-[1.5px] border-ink bg-surface px-4 py-3 text-left text-muted hover:border-accent focus-visible:border-accent focus-visible:outline-none">
        <span>查選手或賽事,例如「王○明」「武嶺」</span>
        <span aria-hidden="true" className="font-mono text-xs">搜尋 →</span>
      </button>
    </section>
  );
}
