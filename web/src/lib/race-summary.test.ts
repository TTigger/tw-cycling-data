import { describe, it, expect } from "vitest";
import { summarizeRace, durationText } from "./race-summary";
import type { DetailRow } from "./types";

const row = (t: number | null, cat: string | null = null): DetailRow =>
  ({ rank: null, bib: null, name: null, cat, g: null, ag: null, team: null, t, label: null });

describe("summarizeRace", () => {
  const rows = [row(100), row(300), row(200), row(null)];

  it("counts finishers, median and winner from timed rows", () => {
    const s = summarizeRace(rows, 2026, undefined, undefined);
    expect(s).toMatchObject({ finishers: 3, group: null, median: 200, winner: 100, ratePct: null, change: null });
  });

  it("quotes median and fastest for the largest division when there are several", () => {
    // 銅礦88: the 親子組 rides a shorter course, so its winner isn't "the fastest"
    const s = summarizeRace([row(9000, "挑戰組"), row(10000, "挑戰組"), row(11000, "挑戰組"), row(6751, "親子組")],
                            2026, undefined, undefined);
    expect(s).toMatchObject({ finishers: 4, group: "挑戰組", groupFinishers: 3, median: 10000, winner: 9000 });
  });

  it("reports completion rate when present", () => {
    const s = summarizeRace(rows, 2026, { fin: 247, total: 294, rate: 0.84, counts: {} }, undefined);
    expect(s.ratePct).toBe(84);
  });

  it("compares the largest like-for-like division with the previous edition", () => {
    // 銅礦88 挑戰組 2025 -> 2026
    const cy = {
      挑戰組: [{ y: 2025, winner: 10240, median: 16298, p25: 0, p75: 0, n: 280 },
              { y: 2026, winner: 10111, median: 15824, p25: 0, p75: 0, n: 200 }],
      親子組: [{ y: 2025, winner: 0, median: 10696, p25: 0, p75: 0, n: 42 },
              { y: 2026, winner: 0, median: 9265, p25: 0, p75: 0, n: 55 }],
    };
    const s = summarizeRace(rows, 2026, undefined, cy);
    expect(s.change).toEqual({ group: "挑戰組", prevYear: 2025, deltaSec: -474, deltaPct: -2.9 });
  });

  it("makes no claim when fields differ too much or the move is implausible", () => {
    const cy = {
      // 96 武嶺 2025 (bravelog) vs 2026 (PDF): field 252 -> 43
      市民競賽組: [{ y: 2025, winner: 0, median: 13614, p25: 0, p75: 0, n: 252 },
                  { y: 2026, winner: 0, median: 11469, p25: 0, p75: 0, n: 43 }],
      // similar size, but -22%: divisions were redrawn, not a real speed-up
      競賽組: [{ y: 2025, winner: 0, median: 9988, p25: 0, p75: 0, n: 190 },
              { y: 2026, winner: 0, median: 7764, p25: 0, p75: 0, n: 204 }],
    };
    expect(summarizeRace(rows, 2026, undefined, cy).change).toBeNull();
  });
});

describe("durationText", () => {
  it("formats differences", () => {
    expect(durationText(-666)).toBe("11 分 06 秒");
    expect(durationText(42)).toBe("42 秒");
    expect(durationText(3700)).toBe("1 小時 01 分");
  });
});
