import { secondsToHMS } from "../../lib/format";
import { durationText, type RaceSummary as Summary } from "../../lib/race-summary";

/** The race page's answer-first header: one sentence, then the key numbers. */
export default function RaceSummary({ s }: { s: Summary }) {
  if (!s.finishers) return null;
  const c = s.change;
  const g = s.group ?? "全體";
  const stats: [string, string][] = [
    ["完賽人數", s.finishers.toLocaleString("en-US")],
    [`${g}中位`, secondsToHMS(s.median)],
    [`${g}最快`, secondsToHMS(s.winner)],
  ];
  if (s.ratePct != null) stats.push(["完賽率", `${s.ratePct}%`]);
  return (
    <section aria-label="本場重點" className="grid gap-4">
      <p className="font-display text-xl leading-snug text-ink sm:text-2xl" style={{ textWrap: "balance" }}>
        {s.finishers.toLocaleString("en-US")} 人完賽,{g}中位 <span className="num text-accent">{secondsToHMS(s.median)}</span>
        {c && Math.abs(c.deltaPct) >= 0.5 && (
          <>,{c.group === s.group ? "" : c.group}比 {c.prevYear} 年{c.deltaSec < 0 ? "快" : "慢"} <span className="text-accent">{durationText(c.deltaSec)}</span>
            <span className="num text-muted text-base">({c.deltaPct > 0 ? "+" : ""}{c.deltaPct}%)</span></>
        )}
        {c && Math.abs(c.deltaPct) < 0.5 && <>,{c.group === s.group ? "" : c.group}跟 {c.prevYear} 年幾乎一樣</>}
      </p>
      <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:flex sm:flex-wrap sm:gap-x-10">
        {stats.map(([k, v]) => (
          <div key={k}>
            <dt className="text-xs text-muted">{k}</dt>
            <dd className="num text-lg text-ink">{v}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
