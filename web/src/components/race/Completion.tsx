import type { Completion as C } from "../../lib/types";
import { completionParts } from "../../lib/completion";

/** Completion-rate block. Only criterium.tw races carry status today; renders
 * nothing when no completion data exists (graceful absence elsewhere). */
export default function Completion({ completion }: { completion?: C }) {
  if (!completion) return null;
  const p = completionParts(completion);
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">完賽率</h2>
      <p className="text-2xl font-semibold">{p.ratePct}%</p>
      <p className="text-sm text-muted">
        完賽 {p.fin} · DNF {p.dnf} · DNS {p.dns}（共 {p.total} 人報到）
      </p>
    </section>
  );
}
