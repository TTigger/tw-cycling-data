import { useMemo, useState } from "react";
import type { ClimbVamEntry } from "../../lib/types";

export default function ClimbKingBoard({ entries }: { entries: ClimbVamEntry[] }) {
  const [g, setG] = useState<"" | "M" | "F">("");
  const ranked = useMemo(
    () => entries.filter((e) => !g || e.g === g).slice(0, 50),
    [entries, g],
  );
  return (
    <div>
      <div className="mb-2 flex gap-2 text-sm">
        {([["", "全部"], ["M", "男"], ["F", "女"]] as const).map(([v, t]) => (
          <button key={v} onClick={() => setG(v)}
            className={`rounded-lg border px-2 py-1 ${g === v ? "border-accent text-accent" : "border-border text-muted hover:text-accent"}`}>
            {t}
          </button>
        ))}
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted">
              <th className="py-1 pr-3 num">#</th><th className="py-1 pr-3">選手</th>
              <th className="py-1 pr-3 num">最佳 VAM</th><th className="py-1 pr-3 num">推算 W/kg</th>
              <th className="py-1 pr-3">達成於</th>
            </tr>
          </thead>
          <tbody>
            {ranked.map((e, i) => (
              <tr key={e.id} className="border-t border-border/60">
                <td className="py-1.5 pr-3 num text-muted">{i + 1}</td>
                <td className="py-1.5 pr-3">
                  <a className="text-ink hover:text-accent" href={`${import.meta.env.BASE_URL.replace(/\/$/, "")}/athletes?id=${e.id}`}>{e.nm}</a>
                </td>
                <td className="py-1.5 pr-3 num text-accent">{e.best_vam}</td>
                <td className="py-1.5 pr-3 num text-muted">{e.best_wkg ?? "—"}</td>
                <td className="py-1.5 pr-3 text-muted">{e.y} {e.climb}{e.conf === "est" ? "*" : ""}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-muted">* 路線數據為估計。選手身分以 TCU/UCI ID 為錨、姓名為輔,點名字看其生涯。</p>
    </div>
  );
}
