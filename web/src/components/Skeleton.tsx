/**
 * Loading placeholder that reserves the page's eventual height so the swap from
 * loading → content doesn't shift layout (keeps CLS low for the client:only
 * island pages). Decorative only — hidden from assistive tech.
 */
export default function Skeleton({ cards = 3, chartH = 220, bare = false }:
  { cards?: number; chartH?: number; bare?: boolean }) {
  return (
    <div className="animate-pulse space-y-5" aria-hidden="true">
      {/* bare = in-page partial load (header already rendered) → cards only */}
      {!bare && <div className="h-9 w-48 rounded bg-border/50" />}
      {!bare && <div className="h-4 w-80 max-w-full rounded bg-border/40" />}
      {Array.from({ length: cards }).map((_, i) => (
        <div key={i} className="rounded-xl border border-border bg-surface p-4">
          <div className="h-5 w-40 rounded bg-border/50" />
          <div className="mt-3 rounded-lg bg-border/25" style={{ height: chartH }} />
        </div>
      ))}
    </div>
  );
}
