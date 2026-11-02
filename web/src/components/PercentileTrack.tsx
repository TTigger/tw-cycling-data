/** Where a result sits in its field: a short track from last (left) to first
 * (right) with a marker at the share of finishers beaten. */
export default function PercentileTrack({ pct, className = "" }: { pct: number; className?: string }) {
  const p = Math.max(0, Math.min(100, pct));
  return (
    <span role="img" aria-label={`贏過 ${p}% 的完賽者`}
      className={`relative inline-block h-1.5 rounded-full bg-border align-middle ${className}`}>
      <span className="absolute inset-y-0 left-0 rounded-full bg-accent/35" style={{ width: `${p}%` }} />
      <span className="absolute -top-1 h-3.5 w-[3px] -translate-x-1/2 rounded-full bg-accent" style={{ left: `${p}%` }} />
    </span>
  );
}
