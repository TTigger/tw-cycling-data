/**
 * Shareable athlete result card. Pure model builders (career / season / race)
 * turn an AthleteDetail into a normalized CardModel — unit-tested; the canvas
 * renderer (drawCard) is DOM-only. Output: a 1080×1080 PNG using only the masked
 * name + public stats (PDPA-safe).
 */
import type { AthleteDetail, AthleteHistoryRow, ClimbVamEntry, AthleteTrait } from "./types";
import { percentileInField } from "./athletes";
import { secondsToHMS } from "./format";

export type CardType = "career" | "season" | "race";

export interface CardModel {
  kicker: string;                               // small top label
  name: string;                                 // masked name
  subtitle: string;                             // year span · team / cat · team
  badge?: string;                               // 特質 · TCU/UCI 串接
  stats: { value: string; label: string }[];    // up to 3 hero stats
  spark?: number[];                             // per-year best percentile (career)
  chips?: string[];                             // race names (season)
  footer: string;
}

const FOOTER = "台灣公路車賽事成績儀表板";

export function specialtyLabel(traits: Record<string, AthleteTrait>): string | null {
  const climb = traits.climb?.pct;
  const flatVals = [traits.road?.pct, traits.crit?.pct].filter((v): v is number => v != null);
  if (climb == null || !flatVals.length) return null;
  const flat = flatVals.reduce((a, b) => a + b, 0) / flatVals.length;
  const d = climb - flat;
  if (d > 8) return "爬坡型";
  if (d < -8) return "平路型";
  return "全能型";
}

function bestPct(rows: AthleteHistoryRow[]): number | null {
  const ps = rows.map((r) => percentileInField(r.rank, r.field)).filter((p): p is number => p != null);
  return ps.length ? Math.max(...ps) : null;
}

/** Years a rider has results in, newest first (for the season picker). */
export function seasonYears(d: AthleteDetail): number[] {
  return [...new Set(d.history.map((r) => r.y).filter((y): y is number => y != null))]
    .sort((a, b) => b - a);
}

export function bestClimb(id: string, vam: ClimbVamEntry[]): ClimbVamEntry | null {
  const mine = vam.filter((e) => e.id === id);
  return mine.length ? mine.reduce((a, b) => (b.best_vam > a.best_vam ? b : a)) : null;
}

export function careerModel(d: AthleteDetail, vam: ClimbVamEntry[] = []): CardModel {
  const years = [...new Set(d.history.map((r) => r.y).filter((y): y is number => y != null))]
    .sort((a, b) => a - b);
  const bp = bestPct(d.history);
  const climb = bestClimb(d.id, vam);
  const sp = specialtyLabel(d.traits);
  const anchor = d.has_rider ? "TCU 串接" : d.has_uci ? "UCI 串接" : undefined;
  const stats = [
    { value: String(d.history.length), label: "出賽場次" },
    { value: bp == null ? "—" : `${bp}%`, label: "生涯最佳贏過" },
  ];
  if (climb) stats.push({ value: String(Math.round(climb.best_vam)), label: `最快爬坡 VAM·${climb.climb}` });
  return {
    kicker: "台灣公路車 · 生涯成績",
    name: d.nm,
    subtitle: `${years[0] ?? "?"}–${years[years.length - 1] ?? "?"} · ${d.history.length} 場`
      + (d.teams.length ? ` · ${d.teams[0]}` : ""),
    badge: [sp, anchor].filter(Boolean).join(" · ") || undefined,
    stats,
    spark: years.length > 1 ? years.map((y) => bestPct(d.history.filter((r) => r.y === y)) ?? 0) : undefined,
    footer: FOOTER,
  };
}

export function seasonModel(d: AthleteDetail, year: number, vam: ClimbVamEntry[] = []): CardModel {
  const rows = d.history.filter((r) => r.y === year);
  const bp = bestPct(rows);
  const climb = bestClimb(d.id, vam.filter((e) => e.y === year));
  const stats = [
    { value: String(rows.length), label: "出賽" },
    { value: bp == null ? "—" : `${bp}%`, label: "最佳贏過" },
  ];
  if (climb) stats.push({ value: String(Math.round(climb.best_vam)), label: `最快爬坡·${climb.climb}` });
  return {
    kicker: `你的 ${year} 賽季`,
    name: d.nm,
    subtitle: d.teams.length ? d.teams[0] : `${rows.length} 場賽事`,
    stats,
    chips: [...new Set(rows.map((r) => r.rn))].slice(0, 5),
    footer: FOOTER,
  };
}

export function raceModel(d: AthleteDetail, idx: number): CardModel {
  const r = d.history[idx];
  const pct = percentileInField(r.rank, r.field);
  const stats: { value: string; label: string }[] = [];
  if (r.t) stats.push({ value: secondsToHMS(r.t), label: "完賽時間" });
  if (r.rank) stats.push({ value: r.field ? `${r.rank}/${r.field}` : String(r.rank), label: "名次" });
  if (pct != null) stats.push({ value: `${pct}%`, label: "贏過全場" });
  return {
    kicker: `${r.y ?? ""} ${r.rn}`.trim(),
    name: d.nm,
    subtitle: [r.cat, r.team].filter(Boolean).join(" · ") || "—",
    stats,
    footer: FOOTER,
  };
}

export function buildModel(
  type: CardType, d: AthleteDetail, vam: ClimbVamEntry[], year: number, raceIdx: number,
): CardModel {
  if (type === "season") return seasonModel(d, year, vam);
  if (type === "race") return raceModel(d, raceIdx);
  return careerModel(d, vam);
}

// ---- canvas renderer (DOM-only) -------------------------------------------
const W = 1080;
const C = { paper: "#FAF9F5", accent: "#D97757", ink: "#2A2722", muted: "#7A7367", border: "#E7E2DA" };

function fit(ctx: CanvasRenderingContext2D, text: string, maxW: number): string {
  if (ctx.measureText(text).width <= maxW) return text;
  let t = text;
  while (t.length > 1 && ctx.measureText(t + "…").width > maxW) t = t.slice(0, -1);
  return t + "…";
}

/** Largest font size ≤ maxPx at which `text` fits maxW (so long times/ranks shrink
 * rather than truncate). Returns the px; leaves ctx.font set to it. */
function fitFont(ctx: CanvasRenderingContext2D, text: string, maxW: number, maxPx: number,
  family: string, weight = 600, minPx = 34): number {
  let px = maxPx;
  ctx.font = `${weight} ${px}px ${family}`;
  while (px > minPx && ctx.measureText(text).width > maxW) {
    px -= 3;
    ctx.font = `${weight} ${px}px ${family}`;
  }
  return px;
}

function drawSpark(ctx: CanvasRenderingContext2D, vals: number[], x: number, y: number, w: number, h: number) {
  const max = Math.max(...vals, 1), min = Math.min(...vals, 0), span = Math.max(max - min, 1);
  const step = w / (vals.length - 1);
  const pts = vals.map((v, i) => [x + i * step, y + h - ((v - min) / span) * h] as const);
  // area
  ctx.beginPath();
  ctx.moveTo(pts[0][0], y + h);
  pts.forEach((p) => ctx.lineTo(p[0], p[1]));
  ctx.lineTo(pts[pts.length - 1][0], y + h);
  ctx.closePath();
  ctx.fillStyle = "rgba(217,119,87,0.12)";
  ctx.fill();
  // line
  ctx.beginPath();
  pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
  ctx.strokeStyle = C.accent;
  ctx.lineWidth = 5;
  ctx.lineJoin = "round";
  ctx.stroke();
  pts.forEach((p) => { ctx.beginPath(); ctx.arc(p[0], p[1], 7, 0, 7); ctx.fillStyle = C.accent; ctx.fill(); });
}

/** Render a CardModel onto a 1080² canvas. Awaits web fonts so CJK/Fraunces draw. */
export async function drawCard(canvas: HTMLCanvasElement, m: CardModel): Promise<void> {
  canvas.width = W;
  canvas.height = W;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  try { await (document as Document & { fonts?: FontFaceSet }).fonts?.ready; } catch { /* no-op */ }

  ctx.fillStyle = C.paper;
  ctx.fillRect(0, 0, W, W);
  ctx.fillStyle = C.accent;
  ctx.fillRect(0, 0, W, 18);

  const pad = 96;
  const innerW = W - pad * 2;
  ctx.textBaseline = "alphabetic";

  ctx.fillStyle = C.accent;
  ctx.font = "600 32px 'Hanken Grotesk','Noto Sans TC',sans-serif";
  ctx.fillText(fit(ctx, m.kicker, innerW), pad, 150);

  ctx.fillStyle = C.ink;
  ctx.font = "600 104px 'Fraunces','Noto Sans TC',serif";
  ctx.fillText(fit(ctx, m.name, innerW), pad, 270);

  ctx.fillStyle = C.muted;
  ctx.font = "400 36px 'Noto Sans TC',sans-serif";
  ctx.fillText(fit(ctx, m.subtitle, innerW), pad, 330);

  if (m.badge) {
    ctx.fillStyle = C.accent;
    ctx.font = "500 32px 'Noto Sans TC',sans-serif";
    ctx.fillText(fit(ctx, m.badge, innerW), pad, 392);
  }

  // hero stats — horizontal row of up to 3
  const top = 470;
  const colW = innerW / m.stats.length;
  const mono = "'Spline Sans Mono','Noto Sans TC',monospace";
  m.stats.forEach((st, i) => {
    const x = pad + i * colW;
    ctx.fillStyle = C.ink;
    fitFont(ctx, st.value, colW - 20, 76, mono);    // shrink long times/ranks to fit
    ctx.fillText(st.value, x, top + 60);
    ctx.fillStyle = C.muted;
    ctx.font = "400 28px 'Noto Sans TC',sans-serif";
    ctx.fillText(fit(ctx, st.label, colW - 12), x, top + 108);
  });

  // body — spark (career) or chips (season)
  if (m.spark && m.spark.length > 1) {
    ctx.fillStyle = C.muted;
    ctx.font = "400 28px 'Noto Sans TC',sans-serif";
    ctx.fillText("逐年最佳「贏過全場 %」", pad, 690);
    drawSpark(ctx, m.spark, pad, 720, innerW, 150);
  } else if (m.chips && m.chips.length) {
    ctx.fillStyle = C.muted;
    ctx.font = "400 28px 'Noto Sans TC',sans-serif";
    ctx.fillText("本季賽事", pad, 690);
    let cy = 740;
    ctx.font = "500 34px 'Noto Sans TC',sans-serif";
    for (const c of m.chips) {
      ctx.fillStyle = C.ink;
      ctx.fillText("· " + fit(ctx, c, innerW - 40), pad, cy);
      cy += 56;
    }
  }

  // footer watermark
  ctx.fillStyle = C.border;
  ctx.fillRect(pad, W - 132, innerW, 2);
  ctx.fillStyle = C.muted;
  ctx.font = "500 30px 'Hanken Grotesk','Noto Sans TC',sans-serif";
  ctx.fillText(m.footer, pad, W - 76);
}
