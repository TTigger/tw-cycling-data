import { useEffect, useMemo, useState } from "react";
import { loadRaceDifficulty } from "../../lib/data-load";
import { raceSeverity, raceSeverityAll, type SeverityVerdict } from "../../lib/difficulty";
import type { RaceDifficultyFile } from "../../lib/types";

const VERDICT_STYLE: Record<SeverityVerdict, string> = {
  嚴苛: "border-accent/60 bg-accent/10 text-accent",
  偏難: "border-amber-400/60 bg-amber-50 text-amber-700 dark:bg-amber-400/10 dark:text-amber-300",
  正常: "border-border text-muted",
  偏易: "border-emerald-400/60 bg-emerald-50 text-emerald-700 dark:bg-emerald-400/10 dark:text-emerald-300",
};
const VERDICT_TEXT: Record<SeverityVerdict, string> = {
  嚴苛: "該屆完賽人數明顯偏少、且中位時間偏慢——很可能受天候/路況等因素影響(本站無報名與 DNF 數,為推估)。",
  偏難: "該屆完賽人數或完賽時間其一明顯偏離歷年,條件可能稍嚴苛。",
  正常: "完賽人數與時間都與歷年相近。",
  偏易: "完賽人數偏多且時間偏快,當屆條件可能較理想。",
};
const pct = (x: number) => `${x > 0 ? "+" : ""}${x}%`;

export default function RaceSeverity({ rk, year }: { rk: string; year: number | null }) {
  const [file, setFile] = useState<RaceDifficultyFile | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let live = true;
    loadRaceDifficulty()
      .then((f) => { if (live) setFile(f); })
      .catch(() => { if (live) setErr(true); });
    return () => { live = false; };
  }, []);

  const diff = file ? file[rk] : undefined;
  const sev = useMemo(() => raceSeverity(diff, year), [diff, year]);
  const all = useMemo(() => raceSeverityAll(diff), [diff]);

  // Non-essential: only races with a multi-year finisher baseline qualify.
  if (err || !file || !diff || !sev) return null;

  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">賽事嚴苛度(完賽異常推估)</h2>
      <p className="mb-3 text-xs text-muted">
        本站僅有完賽者資料(無報名數、無 DNF)。以「完賽人數 vs 歷年中位」與「中位完賽時間 vs 歷年」兩個訊號,推估該屆是否特別嚴苛;僅供參考。
      </p>

      <div className="flex flex-wrap items-center gap-3">
        <span className={`rounded-full border px-3 py-1 text-sm ${VERDICT_STYLE[sev.verdict]}`}>{sev.verdict}</span>
        {sev.group !== "全部" && (
          <span className="ml-2 text-xs text-muted">(以「{sev.group}」組為準)</span>
        )}
        <div className="text-sm text-ink">
          完賽 <span className="num">{sev.n}</span> 人
          <span className="text-muted">(較歷年中位 {sev.baselineN} 人 <span className="num">{pct(sev.finisherDelta)}</span>)</span>
          ・中位時間較歷年 <span className="num">{pct(sev.timeDelta)}</span>
        </div>
      </div>
      <p className="mt-2 text-sm text-muted">{VERDICT_TEXT[sev.verdict]}</p>

      {all.length > 1 && (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted">
                <th className="py-1 pr-3">年</th><th className="py-1 pr-3 num">完賽</th>
                <th className="py-1 pr-3 num">人數 vs 歷年</th><th className="py-1 pr-3 num">時間 vs 歷年</th>
                <th className="py-1 pr-3">判定</th>
              </tr>
            </thead>
            <tbody>
              {all.map((s) => (
                <tr key={s.year} className={`border-t border-border/60 ${s.year === sev.year ? "bg-accent/5" : ""}`}>
                  <td className="py-1.5 pr-3 num text-muted">{s.year}</td>
                  <td className="py-1.5 pr-3 num text-muted">{s.n}</td>
                  <td className="py-1.5 pr-3 num text-muted">{pct(s.finisherDelta)}</td>
                  <td className="py-1.5 pr-3 num text-muted">{pct(s.timeDelta)}</td>
                  <td className="py-1.5 pr-3 text-muted">{s.verdict}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
