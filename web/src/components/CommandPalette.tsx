import { useEffect, useMemo, useRef, useState } from "react";
import { loadRaces, loadAthletes } from "../lib/data-load";
import { searchAthletes } from "../lib/athletes";
import type { RaceIndex, AthleteIndexEntry } from "../lib/types";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");
const isMac = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform);

interface Item { kind: "頁面" | "賽事" | "選手"; label: string; hint?: string; url: string; }

const PAGES: Item[] = [
  { kind: "頁面", label: "總覽", url: "/" },
  { kind: "頁面", label: "探索", url: "/explore" },
  { kind: "頁面", label: "賽事", url: "/race" },
  { kind: "頁面", label: "系列", url: "/series" },
  { kind: "頁面", label: "選手", url: "/athletes" },
  { kind: "頁面", label: "車隊", url: "/teams" },
  { kind: "頁面", label: "傳奇爬坡", url: "/climbs" },
  { kind: "頁面", label: "洞察", url: "/insights" },
  { kind: "頁面", label: "海外賽", url: "/overseas" },
  { kind: "頁面", label: "資料涵蓋", url: "/coverage" },
];

export default function CommandPalette() {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState("");
  const [active, setActive] = useState(0);
  const [races, setRaces] = useState<RaceIndex[] | null>(null);
  const [athletes, setAthletes] = useState<AthleteIndexEntry[] | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const loaded = useRef(false);

  // global shortcut
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      } else if (e.key === "Escape") {
        setOpen(false);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  // lazy-load data + focus on first open
  useEffect(() => {
    if (!open) return;
    setQ(""); setActive(0);
    requestAnimationFrame(() => inputRef.current?.focus());
    if (loaded.current) return;
    loaded.current = true;
    loadRaces().then(setRaces).catch(() => {});
    loadAthletes().then(setAthletes).catch(() => {});
  }, [open]);

  const results = useMemo<Item[]>(() => {
    const query = q.trim();
    const pages = PAGES.filter((p) => !query || p.label.includes(query));
    if (!query) return pages;
    const raceItems: Item[] = (races ?? [])
      .filter((r) => `${r.y} ${r.rn} ${r.s ?? ""}`.includes(query))
      .slice(0, 8)
      .map((r) => ({ kind: "賽事", label: `${r.y} ${r.rn}`, hint: `${r.rows} 筆`,
        // every race is pre-rendered, so link to the crawlable SSG page
        url: `/race/${encodeURIComponent(r.file)}` }));
    const athItems: Item[] = searchAthletes(athletes ?? [], query, 8)
      .map((a) => ({ kind: "選手", label: a.nm,
        // team + UCI in the hint help tell same-masked-name riders apart
        hint: `${a.tm ? a.tm + " · " : ""}${a.y0}–${a.y1} · ${a.n}場${a.uci ? " · UCI" : ""}`,
        url: `/athletes?id=${a.id}` }));
    return [...pages, ...raceItems, ...athItems];
  }, [q, races, athletes]);

  useEffect(() => { setActive(0); }, [q]);

  function go(it: Item | undefined) {
    if (it) window.location.href = base + it.url;
  }

  function onListKey(e: React.KeyboardEvent) {
    if (e.key === "ArrowDown") { e.preventDefault(); setActive((i) => Math.min(i + 1, results.length - 1)); }
    else if (e.key === "ArrowUp") { e.preventDefault(); setActive((i) => Math.max(i - 1, 0)); }
    else if (e.key === "Enter") { e.preventDefault(); go(results[active]); }
  }

  return (
    <>
      <button onClick={() => setOpen(true)} aria-label="開啟搜尋"
        className="flex items-center gap-1.5 rounded-lg border border-border bg-surface px-2.5 py-1 text-xs text-muted hover:border-accent hover:text-accent">
        <span>搜尋</span>
        <kbd aria-hidden="true" className="rounded border border-border px-1 num">{isMac ? "⌘" : "Ctrl"}K</kbd>
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex items-start justify-center bg-black/30 p-4 pt-[12vh]"
          onClick={() => setOpen(false)}>
          <div className="w-full max-w-lg overflow-hidden rounded-xl border border-border bg-surface shadow-xl"
            onClick={(e) => e.stopPropagation()} role="dialog" aria-label="命令面板">
            <input ref={inputRef} value={q} onChange={(e) => setQ(e.target.value)} onKeyDown={onListKey}
              placeholder="搜尋頁面、賽事、選手…"
              className="w-full border-b border-border bg-transparent px-4 py-3 text-sm text-ink outline-none" />
            <ul className="max-h-[50vh] overflow-y-auto py-1">
              {results.length === 0 && <li className="px-4 py-3 text-sm text-muted">查無結果{!races && q ? "(資料載入中…)" : ""}</li>}
              {results.map((it, i) => (
                <li key={it.url + i}>
                  <button onClick={() => go(it)} onMouseEnter={() => setActive(i)}
                    className={`flex w-full items-center justify-between gap-3 px-4 py-2 text-left text-sm ${i === active ? "bg-accent/10 text-accent" : "text-ink"}`}>
                    <span className="flex items-center gap-2 truncate">
                      <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] ${i === active ? "bg-accent/20 text-accent" : "bg-border/40 text-muted"}`}>{it.kind}</span>
                      <span className="truncate">{it.label}</span>
                    </span>
                    {it.hint && <span className="shrink-0 num text-xs text-muted">{it.hint}</span>}
                  </button>
                </li>
              ))}
            </ul>
            <div className="flex items-center justify-between border-t border-border px-4 py-2 text-[11px] text-muted">
              <span>↑↓ 選擇 · ↵ 前往 · Esc 關閉</span>
              <span>{races && athletes ? "賽事/選手已載入" : "載入資料中…"}</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
