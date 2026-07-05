import { useEffect, useState } from "react";
import Ridgeline from "../site/Ridgeline";
import { loadHomeRidgeline, loadManifest, type HomeRidgeline } from "../../lib/data-load";
import type { ManifestStats } from "../../lib/types";

export default function HomeHero() {
  const [rl, setRl] = useState<HomeRidgeline | null>(null);
  const [stats, setStats] = useState<ManifestStats | null>(null);
  useEffect(() => {
    loadHomeRidgeline().then(setRl).catch(() => setRl({ unit: "", nodes: [] }));
    loadManifest().then((m) => setStats(m.stats)).catch(() => setStats(null));
  }, []);
  const nodes = rl?.nodes ?? [];
  const fmt = (n: number) => n.toLocaleString("en-US");
  return (
    <section className="relative">
      <div className="relative h-[240px] w-full sm:h-[300px]">
        <Ridgeline variant="hero" data={nodes} height={300} ariaLabel="旗艦賽事中位完賽時間剖面" />
        {/* peak labels overlaid in HTML so text is not stretched by the SVG.
            left aligns to Ridgeline's padded node scale (pad 14 of 1000 -> 1.4%),
            clamped to [5,95]% so edge labels do not clip; long/messy upstream
            names are truncated with the full name on hover. */}
        <div className="pointer-events-none absolute inset-0">
          {nodes.map((nd) => {
            const frac = nd.x / Math.max(nodes.length - 1, 1);
            const left = Math.min(95, Math.max(5, 1.4 + frac * 97.2));
            return (
              <span key={nd.x} title={nd.label}
                className="absolute max-w-[84px] -translate-x-1/2 translate-y-1 truncate font-mono text-[11px] text-muted"
                style={{ left: `${left}%`, bottom: 0 }}>
                {nd.label}
              </span>
            );
          })}
        </div>
      </div>
      <p className="eyebrow mt-6">TAIWAN ROAD CYCLING · 完賽數據</p>
      <h1 className="display-xl mt-2 text-ink">台灣公路賽事,<br />十七年的完賽數據</h1>
      <p className="mt-4 max-w-[46ch] text-lg text-muted">
        查你的成績落在同齡第幾、這場多年來變快了嗎,並自由取用整份開放資料。
      </p>
      <div className="mt-6 flex flex-wrap gap-3">
        <a href="/race" className="rounded-lg bg-accent px-5 py-2.5 font-medium text-bg hover:opacity-90">探索賽事 →</a>
        <a href="/api" className="rounded-lg border border-ink px-5 py-2.5 font-medium text-ink hover:border-accent hover:text-accent">取用開放資料</a>
      </div>
      {stats && (
        <p className="mt-6 font-mono text-sm tabular-nums text-muted">
          {fmt(stats.records)} 完賽 · {fmt(stats.races)} 賽事 · {stats.year_min}–{stats.year_max} · {stats.sources} 來源
        </p>
      )}
    </section>
  );
}
