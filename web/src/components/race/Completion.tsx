import type { Completion as C } from "../../lib/types";
import { completionParts } from "../../lib/completion";

/** Completion-rate block. Only criterium.tw races carry status today; renders
 * nothing when no completion data exists (graceful absence elsewhere). */
export default function Completion({ completion }: { completion?: C }) {
  if (!completion) return null;
  const p = completionParts(completion);
  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">完賽率 {p.ratePct}%</h2>
      <p className="text-sm text-muted mt-1">
        完賽 {p.fin} / 報到 {p.total} 人
      </p>
      <p className="text-sm text-muted">
        未完賽 {p.notFinished} · 未出發 {p.notStarted}
      </p>
    </section>
  );
}
