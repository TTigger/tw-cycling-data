import { describe, it, expect } from "vitest";
import { isTemplated, endpointPreview, curlExample, pythonExample } from "./api-explorer";

describe("isTemplated", () => {
  it("flags templated detail paths", () => {
    expect(isTemplated("race/{race_key}.json")).toBe(true);
    expect(isTemplated("races.json")).toBe(false);
  });
});

describe("endpointPreview", () => {
  it("summarises an array and shows the first element", () => {
    const r = endpointPreview([{ a: 1 }, { a: 2 }, { a: 3 }]);
    expect(r.summary).toContain("3");          // count present
    expect(r.body).toContain('"a": 1');        // first element pretty-printed
    expect(r.body).not.toContain('"a": 2');    // only the first element
  });
  it("summarises an object by its top-level keys", () => {
    const r = endpointPreview({ x: 1, y: 2 });
    expect(r.summary).toContain("x");
    expect(r.body).toContain('"x": 1');
  });
  it("truncates long bodies with an ellipsis", () => {
    const big = [{ s: "z".repeat(5000) }];
    const r = endpointPreview(big, 200);
    expect(r.body.length).toBeLessThanOrEqual(201);  // 200 + ellipsis char
    expect(r.body.endsWith("…")).toBe(true);
  });
  it("handles empty/null safely", () => {
    expect(endpointPreview([]).summary).toContain("0");
    expect(() => endpointPreview(null)).not.toThrow();
  });
});

describe("examples", () => {
  it("embed base + path", () => {
    const base = "https://tw-cycling-data.vercel.app/data/v1";
    expect(curlExample(base, "races.json")).toContain(`${base}/races.json`);
    expect(pythonExample(base, "races.json")).toContain(`${base}/races.json`);
  });
});
