import { useEffect, useMemo, useState } from "react";
import { loadCourseRecords } from "../../lib/data-load";
import { boardOptions, genderRecords, type GenderFilter } from "../../lib/course-records";
import { secondsToHMS } from "../../lib/format";
import type { CourseRecordsFile } from "../../lib/types";
import Skeleton from "../Skeleton";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");
const GENDERS: { key: GenderFilter; label: string }[] = [
  { key: "all", label: "全部" }, { key: "M", label: "男" }, { key: "F", label: "女" },
];

export default function CourseRecords() {
  const [file, setFile] = useState<CourseRecordsFile | null>(null);
  const [rk, setRk] = useState<string>("");
  const [g, setG] = useState<GenderFilter>("all");

  useEffect(() => {
    loadCourseRecords().then((f) => {
      setFile(f);
      setRk(boardOptions(f)[0]?.rk ?? "");
    }).catch(() => {});
  }, []);

  const boards = useMemo(() => (file ? boardOptions(file) : []), [file]);
  const board = file?.[rk];
  // gender data is patchy (many editions never recorded it) — only offer the
  // toggle on boards that actually have both men and women.
  const hasGender = !!board?.records.some((r) => r.g === "M") && !!board?.records.some((r) => r.g === "F");
  const effG = hasGender ? g : "all";
  const rows = useMemo(() => (board ? genderRecords(board, effG) : []), [board, effG]);

  if (!file) return <Skeleton bare cards={1} />;
  if (!boards.length) return null;

  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">🏁 場地最速榜(歷代紀錄)</h2>
      <p className="mb-3 text-xs text-muted">
        僅收錄路線經查證穩定的爬坡賽,跨 2009–2026 所有屆次的最速完賽;每位車手取生涯最佳一次。
        不同組別總距離或有差異,長距離組的完賽時間天生較慢,請對照組別判讀。
      </p>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <select aria-label="選擇爬坡路段" value={rk} onChange={(e) => setRk(e.target.value)}
          className="rounded-lg border border-border bg-bg px-3 py-2 text-sm text-ink">
          {boards.map((b) => (
            <option key={b.rk} value={b.rk}>{b.name}(爬升 {b.elev_m}m · {b.n} 人)</option>
          ))}
        </select>
        {hasGender && (
          <div className="flex gap-1 rounded-lg border border-border p-1 text-sm">
            {GENDERS.map((x) => (
              <button key={x.key} onClick={() => setG(x.key)}
                className={`rounded-md px-3 py-1 ${g === x.key ? "bg-accent/10 text-accent" : "text-muted hover:text-ink"}`}>
                {x.label}
              </button>
            ))}
          </div>
        )}
      </div>

      {rows.length === 0 ? (
        <p className="py-4 text-sm text-muted">此組別無紀錄。</p>
      ) : (
        <>
          <div className="mb-3 rounded-lg border border-accent/40 bg-accent/5 px-4 py-3">
            <div className="text-xs text-accent">👑 現紀錄保持者</div>
            <div className="mt-0.5 flex flex-wrap items-baseline gap-x-3">
              <span className="font-display text-lg text-ink">
                {rows[0].link && rows[0].id
                  ? <a className="hover:text-accent" href={`${base}/athletes?id=${rows[0].id}`}>{rows[0].nm}</a>
                  : rows[0].nm}
              </span>
              <span className="num text-lg text-accent">{secondsToHMS(rows[0].t)}</span>
              <span className="num text-sm text-muted">VAM {rows[0].vam}{rows[0].wkg ? ` · ${rows[0].wkg} W/kg` : ""}</span>
              <span className="text-sm text-muted">{rows[0].y}{rows[0].cat ? ` · ${rows[0].cat}` : ""}</span>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-xs text-muted">
                  <th className="py-1 pr-3 num">#</th><th className="py-1 pr-3">選手</th>
                  <th className="py-1 pr-3 num">完賽</th><th className="py-1 pr-3 num">VAM</th>
                  <th className="py-1 pr-3 num">W/kg</th><th className="py-1 pr-3 num">年</th>
                  <th className="py-1 pr-3">組別</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => (
                  <tr key={r.rank} className="border-t border-border/60">
                    <td className="py-1.5 pr-3 num text-muted">{r.rank}</td>
                    <td className="py-1.5 pr-3">
                      {r.link && r.id
                        ? <a className="text-ink hover:text-accent" href={`${base}/athletes?id=${r.id}`}>{r.nm}</a>
                        : <span className="text-ink">{r.nm}</span>}
                    </td>
                    <td className="py-1.5 pr-3 num text-ink">{secondsToHMS(r.t)}</td>
                    <td className="py-1.5 pr-3 num text-muted">{r.vam}</td>
                    <td className="py-1.5 pr-3 num text-muted">{r.wkg ?? "—"}</td>
                    <td className="py-1.5 pr-3 num text-muted">{r.y ?? "—"}</td>
                    <td className="py-1.5 pr-3 text-muted">{r.cat ?? "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
