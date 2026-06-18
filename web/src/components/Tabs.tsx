export interface TabDef { key: string; label: string }

/** Simple underline tab bar to break long detail pages into sections (less
 * vertical scrolling). Controlled — the parent owns the active key. */
export default function Tabs({ tabs, active, onChange }:
  { tabs: TabDef[]; active: string; onChange: (key: string) => void }) {
  return (
    <div role="tablist" className="flex flex-wrap gap-1 overflow-x-auto border-b border-border">
      {tabs.map((t) => (
        <button key={t.key} role="tab" type="button" aria-selected={active === t.key}
          onClick={() => onChange(t.key)}
          className={`-mb-px shrink-0 border-b-2 px-3 py-2 text-sm transition-colors ${
            active === t.key
              ? "border-accent text-accent"
              : "border-transparent text-muted hover:text-ink"
          }`}>{t.label}</button>
      ))}
    </div>
  );
}
