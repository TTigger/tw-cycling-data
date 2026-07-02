import { describe, it, expect } from "vitest";
import { joyRidges } from "./joyplot";

describe("joyRidges", () => {
  it("first band gets the TOP lane (highest base); bases descend by laneGap", () => {
    const lanes = joyRidges([[10], [20], [30]], 1, 1.6);
    expect(lanes.map((l) => l.base)).toEqual([2, 1, 0]);
  });
  it("scales the global max pct to peak * laneGap", () => {
    const lanes = joyRidges([[10, 40], [20, 5]], 1, 1.6);
    // global max = 40 -> 1.6; others proportional
    expect(lanes[0].scaled[1]).toBeCloseTo(1.6);
    expect(lanes[0].scaled[0]).toBeCloseTo(0.4);
    expect(lanes[1].scaled[0]).toBeCloseTo(0.8);
  });
  it("all-zero pct does not divide by zero (scaled stays 0)", () => {
    const lanes = joyRidges([[0, 0]], 1, 1.6);
    expect(lanes[0].scaled).toEqual([0, 0]);
  });
  it("empty input -> []", () => {
    expect(joyRidges([], 1, 1.6)).toEqual([]);
  });
});
