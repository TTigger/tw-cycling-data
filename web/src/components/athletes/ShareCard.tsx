import { useEffect, useRef, useState } from "react";
import { loadClimbVam } from "../../lib/data-load";
import { buildModel, drawCard, seasonYears, type CardType } from "../../lib/share-card";
import type { AthleteDetail, ClimbVamEntry } from "../../lib/types";

const TYPES: { key: CardType; label: string }[] = [
  { key: "career", label: "生涯" },
  { key: "season", label: "賽季" },
  { key: "race", label: "單場" },
];

export default function ShareCard({ d, onClose }: { d: AthleteDetail; onClose: () => void }) {
  const [type, setType] = useState<CardType>("career");
  const [vam, setVam] = useState<ClimbVamEntry[]>([]);
  const years = seasonYears(d);
  const [year, setYear] = useState(years[0] ?? 0);
  const [raceIdx, setRaceIdx] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => { loadClimbVam().then(setVam).catch(() => {}); }, []);

  useEffect(() => {
    const c = canvasRef.current;
    if (c) drawCard(c, buildModel(type, d, vam, year, raceIdx));
  }, [type, d, vam, year, raceIdx]);

  function download() {
    const c = canvasRef.current;
    if (!c) return;
    c.toBlob((blob) => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `成績卡-${type}.png`;
      a.click();
      URL.revokeObjectURL(url);
    }, "image/png");
  }

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/30 p-4 py-[6vh]"
      onClick={onClose}>
      <div className="w-full max-w-md rounded-xl border border-border bg-surface p-4 shadow-xl"
        onClick={(e) => e.stopPropagation()} role="dialog" aria-label="成績卡">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-display text-lg text-ink">分享成績卡</h2>
          <button onClick={onClose} aria-label="關閉" className="text-muted hover:text-accent">✕</button>
        </div>

        <div className="mb-3 flex gap-1 rounded-lg border border-border p-1 text-sm">
          {TYPES.map((t) => (
            <button key={t.key} onClick={() => setType(t.key)}
              className={`flex-1 rounded-md px-2 py-1 ${type === t.key ? "bg-accent/10 text-accent" : "text-muted hover:text-ink"}`}>
              {t.label}
            </button>
          ))}
        </div>

        {type === "season" && years.length > 0 && (
          <select value={year} onChange={(e) => setYear(Number(e.target.value))}
            className="mb-3 w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-ink">
            {years.map((y) => <option key={y} value={y}>{y} 賽季</option>)}
          </select>
        )}
        {type === "race" && (
          <select value={raceIdx} onChange={(e) => setRaceIdx(Number(e.target.value))}
            className="mb-3 w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-ink">
            {d.history.map((r, i) => <option key={i} value={i}>{r.y} {r.rn}</option>)}
          </select>
        )}

        <canvas ref={canvasRef}
          className="mx-auto block w-full max-w-[360px] rounded-lg border border-border" />

        <button onClick={download}
          className="mt-3 w-full rounded-lg border border-accent bg-accent/10 px-4 py-2 text-sm text-accent hover:bg-accent/20">
          下載 PNG ↓
        </button>
        <p className="mt-2 text-center text-xs text-muted">僅含遮罩姓名與公開成績,可安心分享</p>
      </div>
    </div>
  );
}
