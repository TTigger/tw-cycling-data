export interface RidgeNode { label?: string; x: number; y: number; meta?: Record<string, unknown>; }
export interface RidgelineGeometry {
  width: number; height: number; d: string; area: string;
  nodes: { cx: number; cy: number; node: RidgeNode }[];
}

const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Deterministic ridgeline geometry: data points -> smoothed SVG path + node
 * coordinates. Higher y renders as a taller peak (smaller cy). Pure, no DOM. */
export function ridgelinePath(points: RidgeNode[], width: number, height: number, pad = 8): RidgelineGeometry {
  const n = points.length;
  const xs = points.map((p) => p.x), ys = points.map((p) => p.y);
  const xMin = Math.min(...xs), xMax = Math.max(...xs);
  const yMin = Math.min(...ys), yMax = Math.max(...ys);
  const spanX = xMax - xMin || 1, spanY = yMax - yMin || 1;
  const left = pad, right = width - pad, top = pad, bottom = height - pad;

  const nodes = points.map((p, i) => {
    const cx = n === 1 ? width / 2 : lerp(left, right, (p.x - xMin) / spanX);
    const cy = n === 1 ? (top + bottom) / 2 : lerp(bottom, top, (p.y - yMin) / spanY);
    return { cx, cy, node: p };
  });

  if (n === 1) {
    const { cx, cy } = nodes[0];
    const d = `M ${cx.toFixed(2)} ${cy.toFixed(2)}`;
    return { width, height, d, area: `${d} L ${cx.toFixed(2)} ${bottom.toFixed(2)} Z`, nodes };
  }

  // Catmull-Rom -> cubic bezier for a smooth ridgeline.
  const pt = nodes.map((p) => [p.cx, p.cy] as const);
  let d = `M ${pt[0][0].toFixed(2)} ${pt[0][1].toFixed(2)}`;
  for (let i = 0; i < pt.length - 1; i++) {
    const p0 = pt[i - 1] ?? pt[i], p1 = pt[i], p2 = pt[i + 1], p3 = pt[i + 2] ?? p2;
    const c1x = p1[0] + (p2[0] - p0[0]) / 6, c1y = p1[1] + (p2[1] - p0[1]) / 6;
    const c2x = p2[0] - (p3[0] - p1[0]) / 6, c2y = p2[1] - (p3[1] - p1[1]) / 6;
    d += ` C ${c1x.toFixed(2)} ${c1y.toFixed(2)}, ${c2x.toFixed(2)} ${c2y.toFixed(2)}, ${p2[0].toFixed(2)} ${p2[1].toFixed(2)}`;
  }
  const area = `${d} L ${right.toFixed(2)} ${bottom.toFixed(2)} L ${left.toFixed(2)} ${bottom.toFixed(2)} Z`;
  return { width, height, d, area, nodes };
}
