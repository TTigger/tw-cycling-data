import { useEffect, useId, useRef, useState } from "react";
import { ridgelinePath, type RidgeNode } from "../../lib/ridgeline";

const VIEW_W = 1000;

/** The site signature: one continuous line that is both decoration and data.
 * variant "hero" draws on load and labels peaks; "divider" is a hairline;
 * "inline" is a compact profile for cards. Respects reduced-motion. */
export default function Ridgeline({
  variant = "hero",
  data = [],
  height = variant === "divider" ? 24 : 220,
  className = "",
  ariaLabel = "賽事完賽時間剖面",
}: {
  variant?: "hero" | "divider" | "inline";
  data?: RidgeNode[];
  height?: number;
  className?: string;
  ariaLabel?: string;
}) {
  const gid = useId().replace(/:/g, "");
  const pad = variant === "divider" ? 2 : 14;
  const pts = data.length ? data : [{ x: 0, y: 0.5 }, { x: 1, y: 0.5 }];
  const g = ridgelinePath(pts, VIEW_W, height, pad);
  const pathRef = useRef<SVGPathElement>(null);
  const [drawn, setDrawn] = useState(false);

  useEffect(() => {
    const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce || variant !== "hero") { setDrawn(true); return; }
    const el = pathRef.current;
    if (!el) return;
    const len = el.getTotalLength();
    el.style.strokeDasharray = String(len);
    el.style.strokeDashoffset = String(len);
    // next frame -> transition to 0
    const r = requestAnimationFrame(() => {
      el.style.transition = "stroke-dashoffset 1200ms cubic-bezier(.22,.61,.36,1)";
      el.style.strokeDashoffset = "0";
      setDrawn(true);
    });
    return () => cancelAnimationFrame(r);
  }, [variant, g.d]);

  return (
    <svg className={className} viewBox={`0 0 ${VIEW_W} ${height}`} preserveAspectRatio="none"
      role="img" aria-label={ariaLabel} style={{ width: "100%", height, display: "block" }}>
      {variant !== "divider" && (
        <path d={g.area} fill={`url(#${gid})`} opacity={0.12} />
      )}
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--accent)" />
          <stop offset="100%" stopColor="transparent" />
        </linearGradient>
      </defs>
      <path ref={pathRef} d={g.d} fill="none"
        stroke={variant === "divider" ? "var(--border)" : "var(--accent)"}
        strokeWidth={variant === "divider" ? 1 : 2}
        strokeLinecap="round" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
      {variant === "hero" && drawn && g.nodes.map((nd, i) => (
        <g key={i}>
          <circle cx={nd.cx} cy={nd.cy} r={3.5} fill="var(--bg)" stroke="var(--accent)" strokeWidth={2}
            vectorEffect="non-scaling-stroke" />
        </g>
      ))}
    </svg>
  );
}
