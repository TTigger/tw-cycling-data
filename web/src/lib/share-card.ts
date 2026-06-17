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
// Distinct metallic palettes (clearly different hues so tiers read at a glance):
// bg1→bg2 = the card gradient, glow = the radial highlight, frame = border,
// ink = readable dark text on that metal, accent = sub-label colour.
export const TIER_META: Record<Tier, {
  label: string; bg1: string; bg2: string; frame: string; glow: string;
  ink: string; accent: string; pill1: string; pill2: string; holo?: string[];
}> = {
  // top tier = iridescent/holographic pearl (clearly ≠ plain silver)
  platinum: { label: "白金 PLATINUM", bg1: "#EFF3F9", bg2: "#C7D4E4", frame: "#AEC0D4",
    glow: "rgba(220,232,248,0.7)", ink: "#283341", accent: "#46618A", pill1: "#F2F7FD", pill2: "#C4D4E6",
    holo: ["#BCE7FF", "#CFBCFF", "#FFC6E6", "#C6F6DB", "#FFE7B8"] },
  // refined deep champagne gold (warmer/richer, not flat lemon-yellow)
  gold: { label: "金 GOLD", bg1: "#F6EAC4", bg2: "#C6922E", frame: "#AC8020",
    glow: "rgba(244,222,150,0.7)", ink: "#473307", accent: "#8A5A0F", pill1: "#F3E2A0", pill2: "#CB9C33" },
  // plain neutral silver — no iridescence, so it never reads like platinum
  silver: { label: "銀 SILVER", bg1: "#EFF1F4", bg2: "#BBC1CA", frame: "#A0A8B3",
    glow: "rgba(200,206,214,0.55)", ink: "#333A43", accent: "#5A636E", pill1: "#E7EAEF", pill2: "#B0B7C1" },
  bronze: { label: "銅 BRONZE", bg1: "#F6E3C7", bg2: "#C5824A", frame: "#A3622D",
    glow: "rgba(214,156,96,0.7)", ink: "#46300F", accent: "#955722", pill1: "#EEC79A", pill2: "#C57F47" },
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

  rule(ctx, W - 128);
  ctx.textAlign = "left"; ctx.fillStyle = C.muted; ctx.font = `500 30px 'Hanken Grotesk',${SANS}`;
  ctx.fillText(m.footer, PAD, W - 74);
}

function roundRectPath(ctx: CanvasRenderingContext2D, x: number, y: number, w: number, h: number, r: number) {
  ctx.beginPath(); ctx.roundRect(x, y, w, h, r);
}

/** Render the power card (戰力卡) — a premium tier card. full=false drops the
 * attribute row + rival/VAM. An optional in-memory photo is the avatar (never
 * stored); with no photo there is no avatar block. */
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
  const INK = t.ink;

  // 1) full-bleed metallic gradient
  const bg = ctx.createLinearGradient(0, 0, W * 0.35, W);
  bg.addColorStop(0, t.bg1); bg.addColorStop(1, t.bg2);
  ctx.fillStyle = bg; ctx.fillRect(0, 0, W, W);

  // 1b) iridescent holographic sheen (top tier only — sets it apart from silver)
  if (t.holo) {
    ctx.save();
    ctx.globalAlpha = 0.36;
    ctx.translate(cx, cx); ctx.rotate(-Math.PI / 6); ctx.translate(-cx, -cx);
    const ig = ctx.createLinearGradient(-220, 0, W + 220, 0);
    t.holo.forEach((h, i) => ig.addColorStop(i / (t.holo!.length - 1), h));
    ctx.fillStyle = ig; ctx.fillRect(-220, -220, W + 440, W + 440);
    ctx.restore();
  }

  // 2) radial glow, upper-centre
  const glow = ctx.createRadialGradient(cx, 360, 20, cx, 360, 690);
  glow.addColorStop(0, t.glow); glow.addColorStop(1, "rgba(255,255,255,0)");
  ctx.fillStyle = glow; ctx.fillRect(0, 0, W, W);

  // 3) diagonal foil sheen — brighter, more streaks for shine
  ctx.save();
  ctx.translate(cx, cx); ctx.rotate(-Math.PI / 5); ctx.translate(-cx, -cx);
  for (const [x, w, a] of [[-180, 130, 0.12], [120, 64, 0.24], [430, 150, 0.10], [820, 120, 0.16]] as const) {
    const f = ctx.createLinearGradient(x, 0, x + w, 0);
    f.addColorStop(0, "rgba(255,255,255,0)");
    f.addColorStop(0.5, `rgba(255,255,255,${a})`);
    f.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = f; ctx.fillRect(x, -420, w, W + 840);
  }
  ctx.restore();

  // 3b) soft edge vignette for depth
  const vg = ctx.createRadialGradient(cx, cx, W * 0.32, cx, cx, W * 0.72);
  vg.addColorStop(0, "rgba(0,0,0,0)"); vg.addColorStop(1, "rgba(0,0,0,0.10)");
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, W);

  // 4) framed border (thick tier frame + inner hairline)
  ctx.lineWidth = 18; ctx.strokeStyle = t.frame;
  roundRectPath(ctx, 28, 28, W - 56, W - 56, 46); ctx.stroke();
  ctx.lineWidth = 3; ctx.strokeStyle = "rgba(255,255,255,0.6)";
  roundRectPath(ctx, 46, 46, W - 92, W - 92, 36); ctx.stroke();

  ctx.textAlign = "center"; ctx.textBaseline = "alphabetic";

  // tier pill
  const pillW = 384, pillH = 64, pillY = 100;
  ctx.save();
  ctx.shadowColor = "rgba(0,0,0,0.18)"; ctx.shadowBlur = 16; ctx.shadowOffsetY = 5;
  const pg = ctx.createLinearGradient(0, pillY, 0, pillY + pillH);
  pg.addColorStop(0, t.pill1); pg.addColorStop(1, t.pill2);
  ctx.fillStyle = pg; roundRectPath(ctx, cx - pillW / 2, pillY, pillW, pillH, 32); ctx.fill();
  ctx.restore();
  ctx.lineWidth = 2; ctx.strokeStyle = "rgba(255,255,255,0.6)";
  roundRectPath(ctx, cx - pillW / 2, pillY, pillW, pillH, 32); ctx.stroke();
  ctx.fillStyle = INK; ctx.font = `800 32px 'Hanken Grotesk',${SANS}`;
  ctx.fillText(`★ ${t.label}`, cx, pillY + 43);

  // avatar (only with a photo)
  if (hasAvatar) {
    const ay = 296, ar = 92;
    ctx.beginPath(); ctx.arc(cx, ay, ar + 7, 0, Math.PI * 2); ctx.fillStyle = t.frame; ctx.fill();
    ctx.save();
    ctx.beginPath(); ctx.arc(cx, ay, ar, 0, Math.PI * 2); ctx.closePath(); ctx.clip();
    const img = opts.photo as HTMLImageElement, s = Math.min(img.width, img.height) || 1;
    ctx.drawImage(img, (img.width - s) / 2, (img.height - s) / 2, s, s, cx - ar, ay - ar, ar * 2, ar * 2);
    ctx.restore();
  }

  // rating hero (the focal number) — with a bright halo for shine
  const ratingY = hasAvatar ? 510 : 372;
  const ratingTxt = m.overall != null ? `${m.overall}` : "—";
  ctx.font = `800 ${hasAvatar ? 132 : 172}px ${MONO}`;
  ctx.save();
  ctx.shadowColor = "rgba(255,255,255,0.95)"; ctx.shadowBlur = 26;
  ctx.fillStyle = INK; ctx.fillText(ratingTxt, cx, ratingY);
  ctx.fillText(ratingTxt, cx, ratingY);  // double-pass to deepen the glow
  ctx.restore();
  ctx.fillStyle = INK; ctx.fillText(ratingTxt, cx, ratingY);  // crisp on top
  ctx.fillStyle = t.accent; ctx.font = `600 28px ${SANS}`;
  ctx.fillText("實力分位 · 贏過全場 % 中位", cx, ratingY + 42);

  // name
  const nameY = ratingY + 128;
  ctx.fillStyle = INK; fitFont(ctx, m.name, W - 260, hasAvatar ? 66 : 78, DISPLAY, 600, 44);
  ctx.textAlign = "center"; ctx.fillText(m.name, cx, nameY);

  // archetype tag
  if (m.archetype) {
    ctx.font = `600 30px ${SANS}`;
    const tw = ctx.measureText(m.archetype).width + 48;
    ctx.fillStyle = "rgba(255,255,255,0.5)";
    roundRectPath(ctx, cx - tw / 2, nameY + 22, tw, 50, 25); ctx.fill();
    ctx.lineWidth = 1.5; ctx.strokeStyle = "rgba(255,255,255,0.65)";
    roundRectPath(ctx, cx - tw / 2, nameY + 22, tw, 50, 25); ctx.stroke();
    ctx.fillStyle = INK; ctx.textBaseline = "middle";
    ctx.fillText(m.archetype, cx, nameY + 48); ctx.textBaseline = "alphabetic";
  }

  // ── bottom-anchored blocks (so nothing crowds the footer) ──
  const hair = (y: number) => { ctx.fillStyle = "rgba(255,255,255,0.5)"; ctx.fillRect(160, y, W - 320, 1); };

  // attributes (traits, FC-style) — full + no avatar + has traits
  if (full && !hasAvatar && m.radar.length) {
    const axes = m.radar.slice(0, 4), n = axes.length, cw = (W - 280) / n;
    hair(722);
    axes.forEach((a, i) => {
      const x = 140 + cw * (i + 0.5);
      ctx.fillStyle = INK; ctx.font = `800 56px ${MONO}`; ctx.fillText(String(Math.round(a.pct)), x, 798);
      ctx.fillStyle = t.accent; ctx.font = `600 27px ${SANS}`; ctx.fillText(a.label, x, 836);
    });
  }

  // career stats row (always)
  const colW = (W - 240) / m.stats.length;
  hair(868);
  m.stats.forEach((st, i) => {
    const x = 120 + colW * (i + 0.5);
    ctx.fillStyle = INK; ctx.font = `700 54px ${MONO}`; ctx.fillText(st.value, x, 902);
    ctx.fillStyle = t.accent; ctx.font = `500 26px ${SANS}`; ctx.fillText(st.label, x, 940);
  });

  // best climb VAM (full)
  if (full && m.vam) {
    ctx.fillStyle = INK; ctx.font = `500 28px ${SANS}`;
    ctx.fillText(`⛰ 最佳爬坡 VAM ${m.vam.value}`, cx, 974);
  }

  // footer
  ctx.fillStyle = t.accent; ctx.font = `500 26px 'Hanken Grotesk',${SANS}`;
  ctx.fillText(m.footer, cx, W - 62);
  ctx.textAlign = "left";
}
