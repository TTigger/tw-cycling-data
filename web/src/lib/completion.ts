import type { Completion } from "./types";

/** Derive display parts from a prebuilt completion object. */
export function completionParts(c: Completion) {
  const total = c.fin + c.dnf + c.dns;
  return { fin: c.fin, dnf: c.dnf, dns: c.dns, total,
           ratePct: Math.round(c.rate * 100) };
}
