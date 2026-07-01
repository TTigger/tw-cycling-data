import { describe, it, expect } from "vitest";
import { ridgelinePath } from "./ridgeline";

describe("ridgelinePath", () => {
  const pts = [
    { x: 0, y: 10, label: "A" },
    { x: 1, y: 30, label: "B" },
    { x: 2, y: 20, label: "C" },
  ];
  it("maps x across the padded width and returns a node per point", () => {
    const g = ridgelinePath(pts, 300, 100, 10);
    expect(g.nodes).toHaveLength(3);
    expect(g.nodes[0].cx).toBeCloseTo(10);        // first at left pad
    expect(g.nodes[2].cx).toBeCloseTo(290);       // last at width - pad
  });
  it("puts the highest y value at the smallest cy (tallest peak)", () => {
    const g = ridgelinePath(pts, 300, 100, 10);
    const cyB = g.nodes[1].cy, cyA = g.nodes[0].cy;
    expect(cyB).toBeLessThan(cyA);                // y=30 peaks above y=10
    expect(g.nodes[1].cy).toBeCloseTo(10);        // max y -> top pad
    expect(g.nodes[0].cy).toBeCloseTo(90);        // min y -> bottom pad
  });
  it("returns an svg path starting with a move and a closed area", () => {
    const g = ridgelinePath(pts, 300, 100, 10);
    expect(g.d.startsWith("M")).toBe(true);
    expect(g.area.startsWith("M")).toBe(true);
    expect(g.area.trimEnd().endsWith("Z")).toBe(true);
  });
  it("handles a single point without NaN", () => {
    const g = ridgelinePath([{ x: 0, y: 5 }], 100, 40, 8);
    expect(g.nodes[0].cx).toBeCloseTo(50);        // single -> centered
    expect(Number.isNaN(g.nodes[0].cy)).toBe(false);
  });
});
