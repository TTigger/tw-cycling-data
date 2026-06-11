import { describe, it, expect } from "vitest";
import { vam, wkgEstimate, isPlausibleVam } from "./vam";

describe("vam", () => {
  it("vertical metres per hour = elev / hours", () => {
    expect(vam(3275, 3600 * 4)).toBe(819);        // 3275m in 4h
    expect(vam(2900, 9000)).toBe(1160);           // 2900m in 2.5h
  });
  it("null on bad input", () => {
    expect(vam(3000, 0)).toBeNull();
    expect(vam(3000, -5)).toBeNull();
    expect(vam(null as unknown as number, 3600)).toBeNull();
  });
});

describe("wkgEstimate", () => {
  it("Ferrari estimate from vam + grade", () => {
    // 1500 / (100*(2 + 5/10)) = 1500/250 = 6.0
    expect(wkgEstimate(1500, 5)).toBe(6);
    expect(wkgEstimate(null, 5)).toBeNull();
  });
});

describe("isPlausibleVam", () => {
  it("keeps 100..3000, drops outliers", () => {
    expect(isPlausibleVam(1200)).toBe(true);
    expect(isPlausibleVam(50)).toBe(false);
    expect(isPlausibleVam(5000)).toBe(false);
    expect(isPlausibleVam(null)).toBe(false);
  });
});
