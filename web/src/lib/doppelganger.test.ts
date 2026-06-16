import { describe, it, expect } from "vitest";
import {
  doppelgangers, fingerprintDistance, similarity, fingerprintLean,
} from "./doppelganger";
import type { AthleteFeature } from "./types";

function f(id: string, g: "M" | "F", v: number[]): AthleteFeature {
  return { id, g, v };
}

describe("fingerprintDistance / similarity", () => {
  it("identical fingerprints have zero distance and 100% similarity", () => {
    const v = [1, -1, 0.5, 0.2, 0];
    expect(fingerprintDistance(v, v)).toBe(0);
    expect(similarity(0)).toBe(100);
  });
  it("similarity decreases monotonically with distance", () => {
    expect(similarity(1)).toBeGreaterThan(similarity(3));
    expect(similarity(3)).toBeGreaterThan(similarity(6));
  });
});

describe("doppelgangers", () => {
  const feats = [
    f("self", "M", [1, 1, 1, 1, 1]),
    f("near", "M", [1.1, 0.9, 1, 1, 1]),       // closest M
    f("far", "M", [-2, -2, -2, -2, -2]),       // distant M
    f("female", "F", [1, 1, 1, 1, 1]),         // identical but wrong gender
  ];

  it("excludes the target itself", () => {
    expect(doppelgangers(feats, "self").some((d) => d.id === "self")).toBe(false);
  });
  it("only returns same-gender riders", () => {
    expect(doppelgangers(feats, "self").every((d) => d.id !== "female")).toBe(true);
  });
  it("ranks nearer riders first", () => {
    const out = doppelgangers(feats, "self");
    expect(out[0].id).toBe("near");
    expect(out[0].dist).toBeLessThan(out[1].dist);
  });
  it("caps at k", () => {
    expect(doppelgangers(feats, "self", 1)).toHaveLength(1);
  });
  it("returns empty when target is not in the pool", () => {
    expect(doppelgangers(feats, "ghost")).toEqual([]);
  });
});

describe("fingerprintLean", () => {
  it("labels climb-vs-flat lean", () => {
    expect(fingerprintLean([1.5, 0, 0, 0, 0])).toBe("偏爬坡");
    expect(fingerprintLean([0, 1.5, 0, 0, 0])).toBe("偏平路");
    expect(fingerprintLean([0.2, 0, 0, 0, 0])).toBe("全能");
  });
});
