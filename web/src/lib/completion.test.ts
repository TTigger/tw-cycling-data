import { describe, it, expect } from "vitest";
import { completionParts } from "./completion";

describe("completionParts", () => {
  it("computes notFinished, notStarted, ratePct with all six codes present", () => {
    const c = {
      fin: 60, total: 100, rate: 0.6,
      counts: { FIN: 60, DNF: 20, DQ: 5, SRT: 5, DNS: 8, NYS: 2 },
    };
    const p = completionParts(c);
    expect(p.fin).toBe(60);
    expect(p.total).toBe(100);
    expect(p.ratePct).toBe(60);
    expect(p.notFinished).toBe(30);   // DNF(20) + DQ(5) + SRT(5)
    expect(p.notStarted).toBe(10);    // DNS(8) + NYS(2)
  });

  it("handles all-finished case", () => {
    const c = { fin: 10, total: 10, rate: 1, counts: { FIN: 10 } };
    const p = completionParts(c);
    expect(p.total).toBe(10);
    expect(p.ratePct).toBe(100);
    expect(p.notFinished).toBe(0);
    expect(p.notStarted).toBe(0);
  });
});
