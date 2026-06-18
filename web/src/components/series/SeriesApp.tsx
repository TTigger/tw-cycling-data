import { useEffect, useMemo, useState } from "react";
import { loadSeries } from "../../lib/data-load";
import { seriesList } from "../../lib/series";
import type { SeriesFile } from "../../lib/types";
import { raceHref } from "../../lib/race-url";
import Skeleton from "../Skeleton";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

function Pill({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button onClick={onClick}
      className={`rounded-full border px-3 py-1 text-sm ${
        active ? "border-accent bg-accent/10 text-accent" : "border-border text-muted hover:border-accent"
      }`}>{children}</button>
  );
}

export default function SeriesApp() {
  const [file, setFile] = useState<SeriesFile | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [sk, setSk] = useState<string | null>(null);
  const [yr, setYr] = useState<string | null>(null);

  useEffect(() => {
    loadSeries().then(setFile).catch((e) => setErr(String(e)));
  }, []);

  const list = useMemo(() => (file ? seriesList(file) : []), [file]);
  const activeKey = sk && file?.[sk] ? sk : list[0]?.key ?? null;
  const seasons = activeKey ? list.find((s) => s.key === activeKey)!.seasons : [];
  const activeYr = yr && seasons.includes(yr) ? yr : seasons[0] ?? null;
  const season = file && activeKey && activeYr ? file[activeKey].seasons[activeYr] : null;

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!file) return <Skeleton cards={3} />;
  if (!list.length) return <p className="text-muted">尚無多站系列資料。</p>;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-2">
        {list.map((s) => (
          <Pill key={s.key} active={s.key === activeKey} onClick={() => { setSk(s.key); setYr(null); }}>
            {s.name}<span className="ml-1 num text-xs">{s.seasons.length}季</span>
          </Pill>
        ))}
      </div>

      {seasons.length > 1 && (
        <div className="flex flex-wrap gap-2">
          {seasons.map((y) => (
            <Pill key={y} active={y === activeYr} onClick={() => setYr(y)}>{y}</Pill>
          ))}
        </div>
      )}

      {season && (
        <>
          <section className="rounded-xl border border-border bg-surface p-4">
            <h2 className="font-display text-lg text-ink">{activeYr} 賽季站別({season.stations.length} 站)</h2>
            <div className="mt-2 flex flex-wrap gap-2">
              {season.stations.map((st) => (
                <a key={st.rk} href={raceHref(st.rk, activeYr)}
                  className="rounded-lg border border-border bg-bg px-3 py-1.5 text-sm text-ink hover:border-accent">
                  {st.name}{st.n ? <span className="ml-1 num text-xs text-muted">{st.n}人</span> : null}
                </a>
              ))}
            </div>
          </section>

          <section className="rounded-xl border border-border bg-surface p-4">
            <h2 className="font-display text-lg text-ink">綜合表現總排</h2>
            <p className="mb-2 text-xs text-muted">
              積分 = 各站「贏過全場 %」最佳值之總和(出賽 ≥2 站者列入);此為綜合表現排行,非官方積分制,僅供參考。
            </p>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-muted">
                    <th className="py-1 pr-3 num">#</th><th className="py-1 pr-3">選手</th>
                    <th className="py-1 pr-3 num">出賽站</th><th className="py-1 pr-3 num">積分</th>
                    <th className="py-1 pr-3 num">最佳單站</th>
                  </tr>
                </thead>
                <tbody>
                  {season.standings.map((r, i) => (
                    <tr key={r.id} className="border-t border-border/60">
                      <td className="py-1.5 pr-3 num text-muted">{i + 1}</td>
                      <td className="py-1.5 pr-3">
                        {r.link
                          ? <a className="text-ink hover:text-accent" href={`${base}/athletes?id=${r.id}`}>{r.nm}</a>
                          : <span className="text-ink">{r.nm}</span>}
                      </td>
                      <td className="py-1.5 pr-3 num text-muted">{r.n}</td>
                      <td className="py-1.5 pr-3 num text-ink">{r.pts}</td>
                      <td className="py-1.5 pr-3 num text-muted">{r.best}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
