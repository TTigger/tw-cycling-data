import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { loadClimbVam } from "../../lib/data-load";
import { buildModel, drawCard, powerModel, drawPowerCard, seasonYears, type CardType } from "../../lib/share-card";
import type { AthleteDetail, ClimbVamEntry } from "../../lib/types";

const TYPES: { key: CardType; label: string }[] = [
  { key: "power", label: "戰力" },
  { key: "career", label: "生涯" },
  { key: "season", label: "賽季" },
  { key: "race", label: "單場" },
];

export default function ShareCard({ d, onClose }: { d: AthleteDetail; onClose: () => void }) {
  const [type, setType] = useState<CardType>("power");
  const [vam, setVam] = useState<ClimbVamEntry[]>([]);
  const years = seasonYears(d);
  const [year, setYear] = useState(years[0] ?? 0);
  const [raceIdx, setRaceIdx] = useState(0);
  const [full, setFull] = useState(true);
  const [photo, setPhoto] = useState<HTMLImageElement | null>(null);
  const [customName, setCustomName] = useState("");
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => { loadClimbVam().then(setVam).catch(() => {}); }, []);

  // lock background scroll while the dialog is open
  useEffect(() => {
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => { document.body.style.overflow = prev; };
  }, []);

  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;
    const name = customName.trim() || d.nm;   // user may opt to show their full name
    if (type === "power") {
      const m = powerModel(d, vam); m.name = name;
      drawPowerCard(c, m, { full, photo });
    } else {
      const m = buildModel(type, d, vam, year, raceIdx); m.name = name;
      drawCard(c, m);
    }
  }, [type, d, vam, year, raceIdx, full, photo, customName]);

  function onPhoto(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const img = new Image();
    const url = URL.createObjectURL(file);
    img.onload = () => { setPhoto(img); URL.revokeObjectURL(url); };  // decoded in memory; not uploaded/stored
    img.src = url;
  }

  function download() {
    const c = canvasRef.current;
    if (!c) return;
    c.toBlob((blob) => {
      if (!blob) return;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${type === "power" ? "戰力卡" : `成績卡-${type}`}.png`;
      a.click();
      URL.revokeObjectURL(url);
    }, "image/png");
  }

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 p-4"
      onClick={onClose}>
      <div className="max-h-[92vh] w-full max-w-md overflow-y-auto rounded-xl border border-border bg-surface p-4 shadow-xl"
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

        <div className="mb-3">
          <input value={customName} onChange={(e) => setCustomName(e.target.value)}
            maxLength={24} placeholder={`顯示名稱(預設 ${d.nm})`}
            className="w-full rounded-lg border border-border bg-bg px-3 py-2 text-sm text-ink outline-none focus:border-accent" />
          <p className="mt-1 text-xs text-muted">預設為遮罩姓名;想印完整姓名可自行輸入 —— 只會合成到你下載的卡片,網站不會儲存或公開。</p>
        </div>

        {type === "power" && (
          <div className="mb-3 space-y-2">
            <div className="flex gap-1 rounded-lg border border-border p-1 text-sm">
              {[{ k: true, l: "全上版" }, { k: false, l: "精簡版" }].map((o) => (
                <button key={o.l} onClick={() => setFull(o.k)}
                  className={`flex-1 rounded-md px-2 py-1 ${full === o.k ? "bg-accent/10 text-accent" : "text-muted hover:text-ink"}`}>
                  {o.l}
                </button>
              ))}
            </div>
            <div className="flex items-center gap-2">
              <label className="cursor-pointer rounded-lg border border-border px-3 py-1.5 text-sm text-muted hover:border-accent hover:text-accent">
                📷 上傳照片
                <input type="file" accept="image/*" onChange={onPhoto} className="hidden" />
              </label>
              {photo && (
                <button onClick={() => setPhoto(null)} className="text-xs text-muted hover:text-accent">移除照片</button>
              )}
              <span className="text-xs text-muted">照片只在你瀏覽器內合成,不會上傳或儲存</span>
            </div>
          </div>
        )}

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
        <p className="mt-2 text-center text-xs text-muted">卡片只在你瀏覽器內合成;網站本身僅公開遮罩姓名與成績。</p>
      </div>
    </div>,
    document.body,
  );
}
