/**
 * Shareable athlete result card. Pure model builders (career / season / race)
 * turn an AthleteDetail into a normalized CardModel — unit-tested; the canvas
 * renderer (drawCard) is DOM-only. Output: a 1080×1080 PNG using only the masked
 * name + public stats (PDPA-safe).
 */
import type { AthleteDetail, AthleteHistoryRow, ClimbVamEntry, AthleteTrait } from "./types";
import { percentileInField } from "./athletes";
import { secondsToHMS } from "./format";

export type CardType = "career" | "season" | "race" | "power";

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

// ---- power card (戰力卡) ---------------------------------------------------
export type Tier = "platinum" | "gold" | "silver" | "bronze";
// metallic frame palette per tier (c1 = highlight, c2 = shade)
export const TIER_META: Record<Tier, { label: string; c1: string; c2: string; tint: string }> = {
  platinum: { label: "白金 PLATINUM", c1: "#EEF0F3", c2: "#AEB8C4", tint: "rgba(174,184,196,0.16)" },
  gold: { label: "金 GOLD", c1: "#F6DA7C", c2: "#C7942B", tint: "rgba(199,148,43,0.16)" },
  silver: { label: "銀 SILVER", c1: "#DEDFE2", c2: "#9AA0A6", tint: "rgba(154,160,166,0.16)" },
  bronze: { label: "銅 BRONZE", c1: "#DCAB74", c2: "#9C6B3F", tint: "rgba(156,107,63,0.16)" },
};

/** Strength tier from the career median in-field percentile (贏過全場 %). */
export function tierOf(overallPct: number | null): Tier {
  const p = overallPct ?? 0;
  if (p >= 85) return "platinum";
  if (p >= 70) return "gold";
  if (p >= 50) return "silver";
  return "bronze";
}

function medianPct(rows: AthleteHistoryRow[]): number | null {
  const ps = rows.map((r) => percentileInField(r.rank, r.field))
    .filter((p): p is number => p != null).sort((a, b) => a - b);
  if (!ps.length) return null;
  const m = Math.floor(ps.length / 2);
  return Math.round(ps.length % 2 ? ps[m] : (ps[m - 1] + ps[m]) / 2);
}

const TRAIT_LABEL: Record<string, string> = { climb: "爬坡", road: "公路", crit: "繞圈", tt: "計時" };
const TRAIT_ORDER = ["climb", "road", "crit", "tt"];

export interface PowerRadarAxis { label: string; pct: number; }
export interface PowerModel {
  name: string; tier: Tier; overall: number | null; archetype: string | null; badge?: string;
  radar: PowerRadarAxis[];
  stats: { value: string; label: string }[];
  rival?: { nm: string; w: number; l: number };
  vam?: { value: number; climb: string };
  footer: string;
}

export function powerModel(d: AthleteDetail, vam: ClimbVamEntry[] = []): PowerModel {
  const overall = medianPct(d.history);
  const ranks = d.history.map((r) => r.rank).filter((r): r is number => r != null);
  const wins = ranks.filter((r) => r === 1).length;
  const climb = bestClimb(d.id, vam);
  const anchor = d.has_rider ? "TCU 串接" : d.has_uci ? "UCI 串接" : undefined;
  return {
    name: d.nm, tier: tierOf(overall), overall, archetype: specialtyLabel(d.traits), badge: anchor,
    radar: TRAIT_ORDER.filter((t) => d.traits[t]).map((t) => ({ label: TRAIT_LABEL[t], pct: d.traits[t].pct })),
    stats: [
      { value: String(d.history.length), label: "出賽場次" },
      { value: String(wins), label: "冠軍" },
      { value: ranks.length ? String(Math.min(...ranks)) : "—", label: "最佳名次" },
    ],
    rival: d.rivals?.[0] ? { nm: d.rivals[0].nm, w: d.rivals[0].w, l: d.rivals[0].l } : undefined,
    vam: climb ? { value: Math.round(climb.best_vam), climb: climb.climb } : undefined,
    footer: FOOTER,
  };
}

function radarShape(ctx: CanvasRenderingContext2D, axes: PowerRadarAxis[], cx: number, cy: number, r: number, color: string) {
  const n = axes.length;
  const ang = (i: number) => -Math.PI / 2 + (i / n) * 2 * Math.PI;
  ctx.strokeStyle = "rgba(42,39,34,0.10)";
  ctx.lineWidth = 2;
  for (let ring = 1; ring <= 3; ring++) {
    ctx.beginPath();
    for (let i = 0; i <= n; i++) {
      const rr = (r * ring) / 3, a = ang(i % n);
      const x = cx + rr * Math.cos(a), y = cy + rr * Math.sin(a);
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    }
    ctx.closePath(); ctx.stroke();
  }
  ctx.beginPath();
  axes.forEach((ax, i) => {
    const rr = r * Math.max(0, Math.min(100, ax.pct)) / 100, a = ang(i);
    const x = cx + rr * Math.cos(a), y = cy + rr * Math.sin(a);
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = color + "40"; ctx.fill();
  ctx.strokeStyle = color; ctx.lineWidth = 4; ctx.lineJoin = "round"; ctx.stroke();
  ctx.fillStyle = C.muted; ctx.font = "600 26px 'Noto Sans TC',sans-serif"; ctx.textAlign = "center";
  axes.forEach((ax, i) => {
    const a = ang(i), x = cx + (r + 30) * Math.cos(a), y = cy + (r + 30) * Math.sin(a) + 9;
    ctx.fillText(ax.label, x, y);
  });
  ctx.textAlign = "left";
}

/** Render the power card (戰力卡). full=false drops radar/rival/VAM for a clean
 * minimal card. An optional in-memory photo is drawn as the avatar (never stored). */
export async function drawPowerCard(
  canvas: HTMLCanvasElement, m: PowerModel,
  opts: { full?: boolean; photo?: HTMLImageElement | null } = {},
): Promise<void> {
  const full = opts.full !== false;
  canvas.width = W; canvas.height = W;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  try { await (document as Document & { fonts?: FontFaceSet }).fonts?.ready; } catch { /* no-op */ }
  const t = TIER_META[m.tier];
  const cx = W / 2;

  // metallic tier frame
  const g = ctx.createLinearGradient(0, 0, W, W);
  g.addColorStop(0, t.c1); g.addColorStop(0.5, t.c2); g.addColorStop(1, t.c1);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, W);
  // soft tinted paper inset
  ctx.fillStyle = C.paper;
  ctx.beginPath(); ctx.roundRect(26, 26, W - 52, W - 52, 44); ctx.fill();
  const bg = ctx.createLinearGradient(0, 26, 0, W - 26);
  bg.addColorStop(0, t.tint); bg.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = bg; ctx.beginPath(); ctx.roundRect(26, 26, W - 52, W - 52, 44); ctx.fill();

  // glass panel
  ctx.save();
  ctx.shadowColor = "rgba(42,39,34,0.10)"; ctx.shadowBlur = 40; ctx.shadowOffsetY = 12;
  ctx.fillStyle = "rgba(255,255,255,0.55)";
  ctx.beginPath(); ctx.roundRect(70, 70, W - 140, W - 140, 36); ctx.fill();
  ctx.restore();
  ctx.strokeStyle = "rgba(255,255,255,0.7)"; ctx.lineWidth = 2;
  ctx.beginPath(); ctx.roundRect(70, 70, W - 140, W - 140, 36); ctx.stroke();

  ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";

  // tier pill
  const pillW = 360, pillH = 56, pillY = 116;
  const pg = ctx.createLinearGradient(cx - pillW / 2, 0, cx + pillW / 2, 0);
  pg.addColorStop(0, t.c1); pg.addColorStop(1, t.c2);
  ctx.fillStyle = pg; ctx.beginPath(); ctx.roundRect(cx - pillW / 2, pillY, pillW, pillH, 28); ctx.fill();
  ctx.fillStyle = "#2A2722"; ctx.font = "700 30px 'Hanken Grotesk','Noto Sans TC',sans-serif";
  ctx.fillText(`🏆 ${t.label}`, cx, pillY + 38);

  // avatar — photo (in-memory) or tier-tinted initial
  const ay = 320, ar = 96;
  ctx.save();
  ctx.beginPath(); ctx.arc(cx, ay, ar, 0, Math.PI * 2); ctx.closePath();
  ctx.lineWidth = 8; ctx.strokeStyle = t.c2; ctx.stroke(); ctx.clip();
  if (opts.photo) {
    const img = opts.photo, s = Math.min(img.width, img.height) || 1;
    ctx.drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, cx - ar, ay - ar, ar * 2, ar * 2);
  } else {
    const ag2 = ctx.createLinearGradient(cx - ar, ay - ar, cx + ar, ay + ar);
    ag2.addColorStop(0, t.c1); ag2.addColorStop(1, t.c2);
    ctx.fillStyle = ag2; ctx.fillRect(cx - ar, ay - ar, ar * 2, ar * 2);
    ctx.fillStyle = "rgba(255,255,255,0.85)"; ctx.font = "700 96px 'Fraunces','Noto Sans TC',serif";
    ctx.fillText((m.name || "?").slice(0, 1), cx, ay + 34);
  }
  ctx.restore();

  // name + archetype/overall
  ctx.fillStyle = C.ink; ctx.font = "600 84px 'Fraunces','Noto Sans TC',serif";
  ctx.fillText(fit(ctx, m.name, W - 200), cx, 500);
  ctx.fillStyle = C.accent; ctx.font = "600 38px 'Noto Sans TC',sans-serif";
  const line = [m.archetype, m.overall != null ? `實力分位 ${m.overall}%` : null, m.badge]
    .filter(Boolean).join("  ·  ");
  if (line) ctx.fillText(fit(ctx, line, W - 200), cx, 556);

  if (full && m.radar.length >= 3) {
    radarShape(ctx, m.radar, cx, 686, 120, C.accent);
  } else {
    // minimal / no-radar: big hero 實力分位
    ctx.fillStyle = C.ink; ctx.font = "700 200px 'Spline Sans Mono','Noto Sans TC',monospace";
    ctx.fillText(m.overall != null ? `${m.overall}` : "—", cx, 770);
    ctx.fillStyle = C.muted; ctx.font = "500 34px 'Noto Sans TC',sans-serif";
    ctx.fillText("實力分位(贏過全場 % 中位)", cx, 826);
  }

  // hero stats row (3)
  const sy = full ? 878 : 900;
  const colW = (W - 220) / m.stats.length;
  m.stats.forEach((st, i) => {
    const x = 110 + colW * (i + 0.5);
    ctx.fillStyle = C.ink; ctx.font = "700 60px 'Spline Sans Mono','Noto Sans TC',monospace";
    ctx.fillText(st.value, x, sy);
    ctx.fillStyle = C.muted; ctx.font = "400 26px 'Noto Sans TC',sans-serif";
    ctx.fillText(st.label, x, sy + 40);
  });

  // rival + VAM (full only)
  if (full) {
    const bits: string[] = [];
    if (m.rival) bits.push(`⚔ 宿敵 ${m.rival.nm} ${m.rival.w}–${m.rival.l}`);
    if (m.vam) bits.push(`⛰ VAM ${m.vam.value}`);
    if (bits.length) {
      ctx.fillStyle = C.muted; ctx.font = "500 30px 'Noto Sans TC',sans-serif";
      ctx.fillText(fit(ctx, bits.join("    "), W - 200), cx, 962);
    }
  }

  // footer
  ctx.fillStyle = C.muted; ctx.font = "500 28px 'Hanken Grotesk','Noto Sans TC',sans-serif";
  ctx.fillText(m.footer, cx, W - 56);
  ctx.textAlign = "left";
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
