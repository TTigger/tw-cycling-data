import { useState } from "react";
import { useStore } from "@nanostores/react";
import { $filters, setFilter, EMPTY } from "../../lib/filter-store";
import type { Facets } from "../../lib/aggregate";
import type { RaceIndex } from "../../lib/types";

interface Props { facets: Facets; races: RaceIndex[]; }

function Select({ label, value, options, onChange }: {
  label: string; value: string; options: { v: string; t: string }[]; onChange: (v: string) => void;
}) {
  return (
    <label className="flex min-w-0 flex-col gap-1 text-sm">
      <span className="text-muted">{label}</span>
      <select
        className="w-full max-w-[14rem] rounded-lg border border-border bg-surface px-3 py-2 text-ink"
        value={value}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="">全部</option>
        {options.map((o) => <option key={o.v} value={o.v}>{o.t}</option>)}
      </select>
    </label>
  );
}

export default function FilterBar({ facets, races }: Props) {
  const f = useStore($filters);
  const [open, setOpen] = useState(false);
  const raceOpts = races
    .filter((r) => !f.series || r.s === f.series)
    .map((r) => ({ v: r.rk, t: `${r.y ?? ""} ${r.rn}`.trim() }));
  const seen = new Set<string>();
  const uniqRaceOpts = raceOpts.filter((o) => (seen.has(o.v) ? false : seen.add(o.v)));
  const activeCount = [f.year, f.series, f.race, f.raceClass, f.gender, f.ageGroup]
    .filter((x) => x != null).length;

  return (
    <div className="space-y-3">
      {/* Mobile: collapse filters behind a toggle so charts aren't pushed down. */}
      <div className="flex items-center justify-between sm:hidden">
        <button
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open} aria-controls="explore-filters"
          className="flex items-center gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink"
        >
          篩選
          {activeCount > 0 && (
            <span className="rounded-full bg-accent/15 px-1.5 text-xs text-accent">{activeCount}</span>
          )}
          <span className="text-muted" aria-hidden="true">{open ? "▲" : "▼"}</span>
        </button>
        {activeCount > 0 && (
          <button className="text-sm text-muted hover:text-accent"
            onClick={() => $filters.set({ ...EMPTY })}>清除</button>
        )}
      </div>

      {/* Drawer on mobile (2-col grid when open); inline wrapping bar on >=sm. */}
      <div id="explore-filters"
        className={`${open ? "grid grid-cols-2 gap-3" : "hidden"} sm:flex sm:flex-wrap sm:items-end sm:gap-3`}>
        <Select label="年份" value={f.year != null ? String(f.year) : ""}
          options={facets.years.map((y) => ({ v: String(y), t: String(y) }))}
          onChange={(v) => setFilter("year", v ? Number(v) : null)} />
        <Select label="系列" value={f.series ?? ""}
          options={facets.series.map((s) => ({ v: s, t: s }))}
          onChange={(v) => { setFilter("series", v || null); setFilter("race", null); }} />
        <Select label="賽事" value={f.race ?? ""}
          options={uniqRaceOpts}
          onChange={(v) => setFilter("race", v || null)} />
        <Select label="組別類型" value={f.raceClass ?? ""}
          options={facets.raceClasses.map((c) => ({ v: c, t: c }))}
          onChange={(v) => setFilter("raceClass", v || null)} />
        <Select label="性別" value={f.gender ?? ""}
          options={[{ v: "M", t: "男" }, { v: "F", t: "女" }]}
          onChange={(v) => setFilter("gender", (v as "M" | "F") || null)} />
        <Select label="分齡組" value={f.ageGroup ?? ""}
          options={facets.ageGroups.map((a) => ({ v: a, t: a }))}
          onChange={(v) => setFilter("ageGroup", v || null)} />
        <button
          className="hidden rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-accent sm:block"
          onClick={() => $filters.set({ ...EMPTY })}
        >清除</button>
      </div>
    </div>
  );
}
