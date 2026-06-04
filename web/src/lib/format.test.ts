import { describe, it, expect } from "vitest";
import { secondsToHMS, hmsToSeconds, percentileBeaten } from "./format";

describe("time format", () => {
  it("secondsToHMS", () => {
    expect(secondsToHMS(7231)).toBe("2:00:31");
    expect(secondsToHMS(59)).toBe("0:00:59");
    expect(secondsToHMS(null)).toBe("—");
    expect(secondsToHMS(0)).toBe("0:00:00");
    expect(secondsToHMS(90.7)).toBe("0:01:31");
    expect(secondsToHMS(-5)).toBe("—");
  });
  it("hmsToSeconds", () => {
    expect(hmsToSeconds("2:00:31")).toBe(7231);
    expect(hmsToSeconds("00:14:38")).toBe(878);
    expect(hmsToSeconds("bad")).toBeNull();
    expect(hmsToSeconds("1:30:00XYZ")).toBeNull();
  });
});

describe("percentileBeaten", () => {
  const times = [100, 200, 300, 400, 500];
  it("faster than all -> ~100% beaten", () => {
    expect(percentileBeaten(90, times)).toBe(100);
  });
  it("slower than all -> 0%", () => {
    expect(percentileBeaten(600, times)).toBe(0);
  });
  it("median -> ~40-60%", () => {
    const p = percentileBeaten(300, times);
    expect(p).toBeGreaterThanOrEqual(40);
    expect(p).toBeLessThanOrEqual(60);
  });
  it("exact ties are NOT counted as beaten", () => {
    expect(percentileBeaten(300, [300, 300, 300])).toBe(0);
  });
});
