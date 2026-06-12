import { describe, it, expect } from "vitest";
import {
  careerModel, seasonModel, raceModel, specialtyLabel, bestClimb, seasonYears,
} from "./share-card";
import type { AthleteDetail, ClimbVamEntry, AthleteHistoryRow } from "./types";

function row(p: Partial<AthleteHistoryRow>): AthleteHistoryRow {
  return { y: 2024, rk: "rk", rn: "某賽事", cat: null, g: "M", ag: null, team: null,
    rank: null, t: null, label: null, d: null, field: null, ...p };
}

const D: AthleteDetail = {
  id: "abc", nm: "林○宇", conf: "high", has_uci: false, has_rider: true,
  teams: ["喬家車隊"],
  traits: { climb: { pct: 80, n: 5 }, road: { pct: 60, n: 4 }, crit: { pct: 64, n: 2 } },
  history: [
    row({ y: 2023, rn: "武嶺盃", rank: 5, field: 100 }),     // beat 95%
    row({ y: 2024, rn: "KOM", rank: 50, field: 100 }),       // 50%
    row({ y: 2024, rn: "彰化100", rank: 10, field: 200 }),   // beat 95%
  ],
};

const VAM: ClimbVamEntry[] = [
  { id: "abc", nm: "林○宇", best_vam: 1180, best_wkg: 4.2, climb: "武嶺", y: 2023, conf: "high", g: "M" },
  { id: "abc", nm: "林○宇", best_vam: 1320, best_wkg: 4.8, climb: "KOM", y: 2024, conf: "high", g: "M" },
  { id: "other", nm: "x", best_vam: 9999, best_wkg: 9, climb: "z", y: 2024, conf: "high", g: "M" },
];

describe("specialtyLabel", () => {
  it("flags climber when climb pct beats flat by >8", () => {
    expect(specialtyLabel(D.traits)).toBe("爬坡型"); // 80 vs (60+64)/2=62 → +18
  });
  it("returns null without flat data", () => {
    expect(specialtyLabel({ climb: { pct: 80, n: 1 } })).toBeNull();
  });
});

describe("bestClimb / seasonYears", () => {
  it("picks this rider's highest VAM, ignores others", () => {
    expect(bestClimb("abc", VAM)?.best_vam).toBe(1320);
    expect(bestClimb("nobody", VAM)).toBeNull();
  });
  it("lists years newest-first", () => {
    expect(seasonYears(D)).toEqual([2024, 2023]);
  });
});

describe("careerModel", () => {
  const m = careerModel(D, VAM);
  it("uses best career percentile and total races", () => {
    expect(m.name).toBe("林○宇");
    expect(m.stats[0]).toEqual({ value: "3", label: "出賽場次" });
    expect(m.stats[1].value).toBe("95%");                  // best of 95/50/95
  });
  it("adds climb VAM stat + specialty/anchor badge + spark", () => {
    expect(m.stats.some((s) => s.value === "1320")).toBe(true);
    expect(m.badge).toContain("爬坡型");
    expect(m.badge).toContain("TCU 串接");
    expect(m.spark?.length).toBe(2);                        // 2023 + 2024
  });
});

describe("seasonModel", () => {
  it("scopes to one year and lists that year's races as chips", () => {
    const m = seasonModel(D, 2024, VAM);
    expect(m.kicker).toBe("你的 2024 賽季");
    expect(m.stats[0]).toEqual({ value: "2", label: "出賽" });
    expect(m.chips).toEqual(["KOM", "彰化100"]);
    expect(m.stats.some((s) => s.label.includes("最快爬坡"))).toBe(true); // KOM 2024 climb
  });
});

describe("raceModel", () => {
  it("shows time/rank/percentile for one result", () => {
    const m = raceModel(D, 0); // 武嶺盃 rank 5/100
    expect(m.kicker).toBe("2023 武嶺盃");
    expect(m.stats.find((s) => s.label === "名次")?.value).toBe("5/100");
    expect(m.stats.find((s) => s.label === "贏過全場")?.value).toBe("95%");
  });
});
