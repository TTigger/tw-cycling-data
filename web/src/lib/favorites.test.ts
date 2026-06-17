import { describe, it, expect } from "vitest";
import { toggleBy } from "./favorites";

const k = (x: { id: string }) => x.id;

describe("toggleBy", () => {
  it("adds an absent item to the front", () => {
    expect(toggleBy([{ id: "b" }], { id: "a" }, k)).toEqual([{ id: "a" }, { id: "b" }]);
  });
  it("removes a present item (by key)", () => {
    expect(toggleBy([{ id: "a" }, { id: "b" }], { id: "a" }, k)).toEqual([{ id: "b" }]);
  });
  it("does not duplicate", () => {
    const once = toggleBy([], { id: "a" }, k);
    expect(toggleBy(once, { id: "a" }, k)).toEqual([]);
  });
});
