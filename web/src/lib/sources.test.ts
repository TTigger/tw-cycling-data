import { describe, it, expect } from "vitest";
import { sourceInfo } from "./sources";

describe("sourceInfo", () => {
  it("maps known domains to site name + url", () => {
    expect(sourceInfo("tsu.com.tw").name).toBe("運動筆記");
    expect(sourceInfo("twbike.org").name).toBe("中華民國登山車協會");
    expect(sourceInfo("bravelog.tw").url).toBe("https://www.bravelog.tw/");
  });
  it("falls back to the domain with empty url for unknown sources", () => {
    expect(sourceInfo("unknown.example")).toEqual({ name: "unknown.example", url: "" });
  });
});
