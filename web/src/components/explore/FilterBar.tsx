import { useStore } from "@nanostores/react";
import { $filters, setFilter, EMPTY } from "../../lib/filter-store";
import type { Facets } from "../../lib/aggregate";
import type { RaceIndex } from "../../lib/types";

interface Props { facets: Facets; races: RaceIndex[]; }

function Select({ label, value, options, onChange }: {
  label: string; value: string; options: { v: string; t: string }[]; onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1 text-sm">
      <span className="text-muted">{label}</span>
      <select
        className="rounded-lg border border-border bg-surface px-3 py-2 text-ink"
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
  const raceOpts = races
    .filter((r) => !f.series || r.s === f.series)
    .map((r) => ({ v: r.rk, t: `${r.y ?? ""} ${r.rn}`.trim() }));
  const seen = new Set<string>();
  const uniqRaceOpts = raceOpts.filter((o) => (seen.has(o.v) ? false : seen.add(o.v)));

  return (
    <div className="flex flex-wrap items-end gap-3">
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
        className="rounded-lg border border-border px-3 py-2 text-sm text-muted hover:text-accent"
        onClick={() => $filters.set({ ...EMPTY })}
      >清除</button>
    </div>
  );
}
