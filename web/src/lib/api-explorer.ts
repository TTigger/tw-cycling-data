/** Pure helpers for the /api explorer page — no fetch, fully unit-testable. */

/** A templated detail path needs an id (e.g. race/{race_key}.json). */
export function isTemplated(path: string): boolean {
  return path.includes("{");
}

function truncate(s: string, maxChars: number): string {
  return s.length > maxChars ? s.slice(0, maxChars) + "…" : s;
}

/** Bounded preview of a fetched endpoint: a one-line summary + a pretty-printed,
 * truncated body. For arrays, only the FIRST element is rendered (so a 3.9MB
 * index never floods the DOM). */
export function endpointPreview(
  data: unknown, maxChars = 1500,
): { summary: string; body: string } {
  if (Array.isArray(data)) {
    const first = data.length ? JSON.stringify(data[0], null, 2) : "(空陣列)";
    return { summary: `陣列,共 ${data.length} 筆${data.length ? ";顯示第 1 筆:" : ""}`,
             body: truncate(first, maxChars) };
  }
  if (data && typeof data === "object") {
    const keys = Object.keys(data as Record<string, unknown>);
    const shown = keys.slice(0, 12).join(", ");
    const summary = keys.length > 12
      ? `物件,鍵:${shown} …(共 ${keys.length} 鍵)`
      : `物件,鍵:${shown}`;
    return { summary, body: truncate(JSON.stringify(data, null, 2), maxChars) };
  }
  return { summary: "(無資料)", body: truncate(JSON.stringify(data ?? null, null, 2), maxChars) };
}

export function curlExample(base: string, path: string): string {
  return `curl ${base}/${path}`;
}

export function pythonExample(base: string, path: string): string {
  return `import requests\nr = requests.get("${base}/${path}")\ndata = r.json()`;
}

export function jsExample(base: string, path: string): string {
  return `fetch("${base}/${path}")\n  .then(r => r.json())\n  .then(console.log);`;
}
