import type { ReactNode } from "react";

/** C-format page header for analysis pages: one answer sentence, then a few
 * key numbers. Same look as the race page's summary. */
export default function Lead({ children, stats, note }:
  { children: ReactNode; stats?: [string, string][]; note?: ReactNode }) {
  return (
    <section aria-label="重點" className="grid gap-4">
      <p className="font-display text-xl leading-snug text-ink sm:text-2xl" style={{ textWrap: "balance" }}>
        {children}
      </p>
      {stats && stats.length > 0 && (
        <dl className="grid grid-cols-2 gap-x-6 gap-y-3 sm:flex sm:flex-wrap sm:gap-x-10">
          {stats.map(([k, v]) => (
            <div key={k}>
              <dt className="text-xs text-muted">{k}</dt>
              <dd className="num text-lg text-ink">{v}</dd>
            </div>
          ))}
        </dl>
      )}
      {note && <p className="text-xs text-muted">{note}</p>}
    </section>
  );
}
