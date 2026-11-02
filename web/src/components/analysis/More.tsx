import { useState, type ReactNode } from "react";

/** A secondary chart/table, folded away so the page leads with one answer.
 * Content mounts on first open: charts measure their width on mount, and a
 * closed <details> has none. */
export default function More({ title, hint, children, open = false }:
  { title: string; hint?: string; children: ReactNode; open?: boolean }) {
  const [seen, setSeen] = useState(open);
  return (
    <details className="group border-t border-border py-4" open={open}
      onToggle={(e) => { if ((e.currentTarget as HTMLDetailsElement).open) setSeen(true); }}>
      <summary className="flex cursor-pointer list-none items-baseline justify-between gap-3 [&::-webkit-details-marker]:hidden">
        <span>
          <span className="font-display text-lg text-ink group-hover:text-accent">{title}</span>
          {hint && <span className="ml-2 text-xs text-muted">{hint}</span>}
        </span>
        <span aria-hidden="true" className="font-mono text-sm text-muted transition-transform group-open:rotate-45">+</span>
      </summary>
      {seen && <div className="mt-3">{children}</div>}
    </details>
  );
}
