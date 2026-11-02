import type { Completion } from "./types";

/** Derive display parts from a prebuilt completion object. Groups the six
 * status codes: not-finished = DNF+DQ+SRT, not-started = DNS+NYS. "NF" = did
 * not finish, type unknown (rows restored from the open dataset, which has no
 * per-row status) — reported separately, never split into the two groups. */
export function completionParts(c: Completion) {
  const n = (k: string) => c.counts[k] || 0;
  const notFinished = n("DNF") + n("DQ") + n("SRT");
  const notStarted = n("DNS") + n("NYS");
  const unknown = n("NF");
  return { fin: c.fin, total: c.total, ratePct: Math.round(c.rate * 100),
           notFinished, notStarted, unknown };
}
