import { describe, it, expect } from "vitest";
import { seriesList } from "./series";
import type { SeriesFile } from "./types";

const FILE: SeriesFile = {
  big: {
    name: "大系列",
    seasons: {
      "2024": { stations: [{ rk: "a", name: "A", n: 100 }, { rk: "b", name: "B", n: 100 }], standings: [] },
      "2025": { stations: [{ rk: "c", name: "C", n: 100 }], standings: [] },
    },
  }, // 3 stations total
  small: {
    name: "小系列",
    seasons: { "2025": { stations: [{ rk: "x", name: "X", n: 50 }, { rk: "y", name: "Y", n: 50 }], standings: [] } },
  }, // 2 stations total
};

describe("seriesList", () => {
  it("sorts by total station count desc and lists seasons newest first", () => {
    const list = seriesList(FILE);
    expect(list.map((s) => s.key)).toEqual(["big", "small"]); // 3 stations > 2
    expect(list[0].stations).toBe(3);
    expect(list[0].seasons).toEqual(["2025", "2024"]); // newest first
  });
});
