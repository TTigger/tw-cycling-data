/**
 * Shareable athlete cards. Pure model builders (career / season / race / power)
 * turn an AthleteDetail into a normalized model — unit-tested; the canvas
 * renderers are DOM-only. Output: a 1080×1080 PNG using only the masked name +
 * public stats (PDPA-safe). Design: generous whitespace, one clear hierarchy,
 * a single focal stat per card (Spotify-Wrapped / FC-card inspired).
 */
import type { AthleteDetail, AthleteHistoryRow, ClimbVamEntry, AthleteTrait } from "./types";
import { percentileInField } from "./athletes";
import { secondsToHMS } from "./format";

export type CardType = "career" | "season" | "race" | "power";

export interface CardRow { left: string; right: string; }
export interface CardModel {
  kicker: string;                                // small top label
  name: string;                                  // masked name
  subtitle: string;                              // year span · team / cat · team
  tag?: string;                                  // specialty pill (e.g. 爬坡型) — no source-linkage claims
  stats: { value: string; label: string }[];     // hero stats
  spark?: number[];                              // per-year best percentile (career)
  rows?: CardRow[];                              // per-race results (season)
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

function medianPct(rows: AthleteHistoryRow[]): number | null {
  const ps = rows.map((r) => percentileInField(r.rank, r.field))
    .filter((p): p is number => p != null).sort((a, b) => a - b);
  if (!ps.length) return null;
  const m = Math.floor(ps.length / 2);
  return Math.round(ps.length % 2 ? ps[m] : (ps[m - 1] + ps[m]) / 2);
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
  const years = [...new Set(d.history.map((r) => r.y).filter((y): y is number => y != null))].sort((a, b) => a - b);
  const bp = bestPct(d.history);
  const climb = bestClimb(d.id, vam);
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
    tag: specialtyLabel(d.traits) ?? undefined,
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
  // best result per race that year, strongest placing first
  const byRace = new Map<string, AthleteHistoryRow>();
  for (const r of rows) {
    const cur = byRace.get(r.rk);
    if (!cur || (r.rank ?? Infinity) < (cur.rank ?? Infinity)) byRace.set(r.rk, r);
  }
  const resultRows: CardRow[] = [...byRace.values()]
    .sort((a, b) => (a.rank ?? Infinity) - (b.rank ?? Infinity))
    .map((r) => ({
      left: r.rn,
      right: r.rank != null ? (r.field ? `${r.rank}/${r.field}` : `第 ${r.rank}`) : (r.t ? secondsToHMS(r.t) : "—"),
    }));
  return {
    kicker: `你的 ${year} 賽季`,
    name: d.nm,
    subtitle: d.teams.length ? d.teams[0] : `${rows.length} 場賽事`,
    stats,
    rows: resultRows,
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

const TRAIT_LABEL: Record<string, string> = { climb: "爬坡", road: "公路", crit: "繞圈", tt: "計時" };
const TRAIT_ORDER = ["climb", "road", "crit", "tt"];

export interface PowerRadarAxis { label: string; pct: number; }
export interface PowerModel {
  name: string; tier: Tier; overall: number | null; archetype: string | null;
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
  return {
    name: d.nm, tier: tierOf(overall), overall, archetype: specialtyLabel(d.traits),
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

// ---- canvas renderers (DOM-only) ------------------------------------------
const W = 1080;
const PAD = 112;
const IW = W - PAD * 2;
const C = { paper: "#FAF9F5", accent: "#D97757", ink: "#2A2722", muted: "#7A7367", border: "#E7E2DA" };

function fit(ctx: CanvasRenderingContext2D, text: string, maxW: number): string {
  if (ctx.measureText(text).width <= maxW) return text;
  let t = text;
  while (t.length > 1 && ctx.measureText(t + "…").width > maxW) t = t.slice(0, -1);
  return t + "…";
}

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

function rule(ctx: CanvasRenderingContext2D, y: number, x = PAD, w = IW) {
  ctx.fillStyle = C.border;
  ctx.fillRect(x, y, w, 2);
}

const MONO = "'Spline Sans Mono','Noto Sans TC',monospace";
const SANS = "'Noto Sans TC',sans-serif";
const DISPLAY = "'Fraunces','Noto Sans TC',serif";

function drawSpark(ctx: CanvasRenderingContext2D, vals: number[], x: number, y: number, w: number, h: number) {
  const max = Math.max(...vals, 1), min = Math.min(...vals, 0), span = Math.max(max - min, 1);
  const step = w / (vals.length - 1);
  const pts = vals.map((v, i) => [x + i * step, y + h - ((v - min) / span) * h] as const);
  ctx.beginPath();
  ctx.moveTo(pts[0][0], y + h);
  pts.forEach((p) => ctx.lineTo(p[0], p[1]));
  ctx.lineTo(pts[pts.length - 1][0], y + h);
  ctx.closePath();
  ctx.fillStyle = "rgba(217,119,87,0.12)";
  ctx.fill();
  ctx.beginPath();
  pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
  ctx.strokeStyle = C.accent;
  ctx.lineWidth = 5;
  ctx.lineJoin = "round";
  ctx.stroke();
  pts.forEach((p) => { ctx.beginPath(); ctx.arc(p[0], p[1], 7, 0, 7); ctx.fillStyle = C.accent; ctx.fill(); });
}

/** Render a career / season / race CardModel onto a 1080² canvas. */
export async function drawCard(canvas: HTMLCanvasElement, m: CardModel): Promise<void> {
  canvas.width = W; canvas.height = W;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  try { await (document as Document & { fonts?: FontFaceSet }).fonts?.ready; } catch { /* no-op */ }

  ctx.fillStyle = C.paper; ctx.fillRect(0, 0, W, W);
  ctx.fillStyle = C.accent; ctx.fillRect(0, 0, W, 14);
  ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";

  // header
  ctx.fillStyle = C.accent; ctx.font = `600 30px 'Hanken Grotesk',${SANS}`;
  ctx.fillText(fit(ctx, m.kicker, IW), PAD, 184);
  ctx.fillStyle = C.ink; fitFont(ctx, m.name, IW, 104, DISPLAY, 600, 52);
  ctx.fillText(m.name, PAD, 300);
  ctx.fillStyle = C.muted; ctx.font = `400 34px ${SANS}`;
  ctx.fillText(fit(ctx, m.subtitle, IW), PAD, 354);
  if (m.tag) {
    ctx.font = `600 30px ${SANS}`;
    const tw = ctx.measureText(m.tag).width + 44;
    ctx.fillStyle = "rgba(217,119,87,0.12)";
    ctx.beginPath(); ctx.roundRect(PAD, 384, tw, 50, 25); ctx.fill();
    ctx.fillStyle = C.accent; ctx.textBaseline = "middle";
    ctx.fillText(m.tag, PAD + 22, 410); ctx.textBaseline = "alphabetic";
  }

  if (m.rows) {
    // season — results list as the focal content
    rule(ctx, 470);
    ctx.fillStyle = C.muted; ctx.font = `500 30px ${SANS}`;
    ctx.fillText(fit(ctx, m.stats.map((s) => `${s.label} ${s.value}`).join("    ·    "), IW), PAD, 532);
    ctx.fillStyle = C.ink; ctx.font = `600 30px ${SANS}`;
    ctx.fillText("本季成績", PAD, 612);
    const MAXR = 7, rh = 56;
    let y = 672;
    m.rows.slice(0, MAXR).forEach((r) => {
      ctx.textAlign = "left"; ctx.fillStyle = C.ink; ctx.font = `500 36px ${SANS}`;
      ctx.fillText(fit(ctx, r.left, IW - 200), PAD, y);
      ctx.textAlign = "right"; ctx.fillStyle = C.accent; ctx.font = `600 34px ${MONO}`;
      ctx.fillText(r.right, W - PAD, y);
      ctx.fillStyle = "rgba(231,226,218,0.8)"; ctx.fillRect(PAD, y + 18, IW, 1);
      y += rh;
    });
    ctx.textAlign = "left";
    if (m.rows.length > MAXR) {
      ctx.fillStyle = C.muted; ctx.font = `400 28px ${SANS}`;
      ctx.fillText(`…還有 ${m.rows.length - MAXR} 場`, PAD, y + 14);
    }
  } else {
    // career / race — big hero stats
    rule(ctx, 456);
    const colW = IW / m.stats.length;
    m.stats.forEach((st, i) => {
      const x = PAD + i * colW;
      ctx.textAlign = "left"; ctx.fillStyle = C.ink;
      fitFont(ctx, st.value, colW - 24, 88, MONO);
      ctx.fillText(st.value, x, 580);
      ctx.fillStyle = C.muted; ctx.font = `400 28px ${SANS}`;
      ctx.fillText(fit(ctx, st.label, colW - 16), x, 628);
    });
    if (m.spark && m.spark.length > 1) {
      rule(ctx, 716);
      ctx.fillStyle = C.muted; ctx.font = `400 30px ${SANS}`;
      ctx.fillText("逐年最佳「贏過全場 %」", PAD, 786);
      drawSpark(ctx, m.spark, PAD, 818, IW, 142);
    }
  }

  // footer
  rule(ctx, W - 128);
  ctx.textAlign = "left"; ctx.fillStyle = C.muted; ctx.font = `500 30px 'Hanken Grotesk',${SANS}`;
  ctx.fillText(m.footer, PAD, W - 74);
}

function radarShape(ctx: CanvasRenderingContext2D, axes: PowerRadarAxis[], cx: number, cy: number, r: number, color: string) {
  const n = axes.length;
  const ang = (i: number) => -Math.PI / 2 + (i / n) * 2 * Math.PI;
  ctx.strokeStyle = "rgba(42,39,34,0.10)"; ctx.lineWidth = 2;
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
  ctx.fillStyle = C.muted; ctx.font = `600 26px ${SANS}`; ctx.textAlign = "center";
  axes.forEach((ax, i) => {
    const a = ang(i), x = cx + (r + 32) * Math.cos(a), y = cy + (r + 32) * Math.sin(a) + 9;
    ctx.fillText(ax.label, x, y);
  });
  ctx.textAlign = "left";
}

/** Render the power card (戰力卡). full=false drops radar/rival/VAM for a clean
 * minimal card. An optional in-memory photo is the avatar (never stored); with
 * no photo there is NO avatar block — the layout breathes instead. */
export async function drawPowerCard(
  canvas: HTMLCanvasElement, m: PowerModel,
  opts: { full?: boolean; photo?: HTMLImageElement | null } = {},
): Promise<void> {
  const full = opts.full !== false;
  const hasAvatar = !!opts.photo;
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
  const pillW = 360, pillH = 58, pillY = 124;
  const pg = ctx.createLinearGradient(cx - pillW / 2, 0, cx + pillW / 2, 0);
  pg.addColorStop(0, t.c1); pg.addColorStop(1, t.c2);
  ctx.fillStyle = pg; ctx.beginPath(); ctx.roundRect(cx - pillW / 2, pillY, pillW, pillH, 29); ctx.fill();
  ctx.fillStyle = "#2A2722"; ctx.font = `700 30px 'Hanken Grotesk',${SANS}`;
  ctx.fillText(`🏆 ${t.label}`, cx, pillY + 39);

  // avatar (only when a photo is supplied)
  let nameY = 330;
  if (hasAvatar) {
    const ay = 330, ar = 100;
    ctx.save();
    ctx.beginPath(); ctx.arc(cx, ay, ar, 0, Math.PI * 2); ctx.closePath();
    ctx.lineWidth = 8; ctx.strokeStyle = t.c2; ctx.stroke(); ctx.clip();
    const img = opts.photo as HTMLImageElement, s = Math.min(img.width, img.height) || 1;
    ctx.drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, cx - ar, ay - ar, ar * 2, ar * 2);
    ctx.restore();
    nameY = 528;
  }

  // name + archetype/overall (no source-linkage text)
  ctx.fillStyle = C.ink; fitFont(ctx, m.name, W - 220, 88, DISPLAY, 600, 48);
  ctx.textAlign = "center"; ctx.fillText(m.name, cx, nameY);
  const sub = [m.archetype, m.overall != null ? `實力分位 ${m.overall}%` : null].filter(Boolean).join("  ·  ");
  if (sub) {
    ctx.fillStyle = C.accent; ctx.font = `600 38px ${SANS}`;
    ctx.fillText(fit(ctx, sub, W - 220), cx, nameY + 58);
  }

  if (full && m.radar.length >= 3) {
    radarShape(ctx, m.radar, cx, hasAvatar ? 706 : 700, 122, C.accent);
  } else {
    ctx.fillStyle = C.ink; ctx.font = `700 196px ${MONO}`;
    ctx.fillText(m.overall != null ? `${m.overall}` : "—", cx, hasAvatar ? 800 : 770);
    ctx.fillStyle = C.muted; ctx.font = `500 34px ${SANS}`;
    ctx.fillText("實力分位(贏過全場 % 中位)", cx, hasAvatar ? 852 : 822);
  }

  // hero stats row (3)
  const sy = full ? 884 : 920;
  const colW = (W - 220) / m.stats.length;
  m.stats.forEach((st, i) => {
    const x = 110 + colW * (i + 0.5);
    ctx.fillStyle = C.ink; ctx.font = `700 60px ${MONO}`;
    ctx.fillText(st.value, x, sy);
    ctx.fillStyle = C.muted; ctx.font = `400 26px ${SANS}`;
    ctx.fillText(st.label, x, sy + 42);
  });

  // rival + VAM (full)
  if (full) {
    const bits: string[] = [];
    if (m.rival) bits.push(`⚔ 宿敵 ${m.rival.nm} ${m.rival.w}–${m.rival.l}`);
    if (m.vam) bits.push(`⛰ VAM ${m.vam.value}`);
    if (bits.length) {
      ctx.fillStyle = C.muted; ctx.font = `500 30px ${SANS}`;
      ctx.fillText(fit(ctx, bits.join("      "), W - 200), cx, 966);
    }
  }

  ctx.fillStyle = C.muted; ctx.font = `500 28px 'Hanken Grotesk',${SANS}`;
  ctx.fillText(m.footer, cx, W - 58);
  ctx.textAlign = "left";
}
