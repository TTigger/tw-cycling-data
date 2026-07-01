import { describe, it, expect } from "vitest";
import { chartColors } from "./chart-colors";

describe("chartColors", () => {
  it("dark mode = terrain green accent + amber secondary", () => {
    const c = chartColors(true);
    expect(c.accent).toBe("#3DBB7A");
    expect(c.secondary).toBe("#F2B84B");
    expect(c.series[0]).toBe("#3DBB7A");
    expect(c.heat[0]).toBe("#12201A");
    expect(c.heat.at(-1)).toBe("#7FE0AE");
  });
  it("light mode = deeper green + deep amber", () => {
    const c = chartColors(false);
    expect(c.accent).toBe("#1E8A56");
    expect(c.secondary).toBe("#B8791C");
    expect(c.ink).toBe("#12181A");
    expect(c.series[0]).toBe("#1E8A56");
    expect(c.heat.at(-1)).toBe("#1E8A56");
  });
  it("series has 6 categorical colors both modes", () => {
    expect(chartColors(true).series).toHaveLength(6);
    expect(chartColors(false).series).toHaveLength(6);
  });
});
