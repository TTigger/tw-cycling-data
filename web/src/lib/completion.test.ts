import { describe, it, expect } from "vitest";
import { completionParts } from "./completion";

describe("completionParts", () => {
  it("computes total and rounded percent", () => {
    expect(completionParts({ fin: 64, dnf: 30, dns: 6, rate: 0.64 })).toEqual({
      fin: 64, dnf: 30, dns: 6, total: 100, ratePct: 64,
    });
  });
  it("handles all-finished", () => {
    const p = completionParts({ fin: 10, dnf: 0, dns: 0, rate: 1 });
    expect(p.total).toBe(10);
    expect(p.ratePct).toBe(100);
  });
});
