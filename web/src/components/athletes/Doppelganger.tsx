import { useEffect, useMemo, useState } from "react";
import { loadAthleteFeatures } from "../../lib/data-load";
import { doppelgangers, fingerprintLean } from "../../lib/doppelganger";
import type { AthleteFeature, AthleteIndexEntry } from "../../lib/types";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

const LEAN_STYLE: Record<string, string> = {
  偏爬坡: "border-accent/50 text-accent",
  偏平路: "border-emerald-400/50 text-emerald-600",
  全能: "border-border text-muted",
};

export default function Doppelganger(
  { targetId, index }: { targetId: string; index: AthleteIndexEntry[] },
) {
  const [feats, setFeats] = useState<AthleteFeature[] | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    let live = true;
    loadAthleteFeatures()
      .then((f) => { if (live) setFeats(f); })
      .catch(() => { if (live) setErr(true); });
    return () => { live = false; };
  }, []);

  const byId = useMemo(() => {
    const m = new Map<string, AthleteIndexEntry>();
    for (const a of index) m.set(a.id, a);
    return m;
  }, [index]);
  const featById = useMemo(() => {
    const m = new Map<string, AthleteFeature>();
    for (const f of feats ?? []) m.set(f.id, f);
    return m;
  }, [feats]);

  const matches = useMemo(
    () => (feats ? doppelgangers(feats, targetId, 6) : []),
    [feats, targetId],
  );

  if (err) return null; // non-essential section — hide if the file fails to load

  const inPool = !!feats && featById.has(targetId);

  return (
    <section className="rounded-xl border border-border bg-surface p-4">
      <h2 className="font-display text-lg text-ink">👯 騎乘分身</h2>
      <p className="mb-3 text-xs text-muted">
        以爬坡 / 平路 / 計時專長、整體實力與年齡帶組成「騎乘指紋」,在同性別選手中找出最相似的 6 位(相似度由指紋距離換算,僅供參考)。
      </p>
      {!feats ? (
        <p className="text-sm text-muted">計算中…</p>
      ) : !inPool || matches.length === 0 ? (
        <p className="text-sm text-muted">此選手出賽資料不足或性別未知,暫時找不到分身。</p>
      ) : (
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {matches.map((m) => {
            const a = byId.get(m.id);
            const feat = featById.get(m.id);
            const lean = feat ? fingerprintLean(feat.v) : "全能";
            return (
              <a key={m.id} href={`${base}/athletes?id=${m.id}`}
                className="rounded-lg border border-border bg-bg p-3 hover:border-accent">
                <div className="flex items-center justify-between gap-2">
                  <span className="font-display text-base text-ink">{a ? a.nm : "選手"}</span>
                  <span className="num text-sm text-accent">{m.sim}%</span>
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-muted">
                  <span className={`rounded-full border px-1.5 py-0.5 ${LEAN_STYLE[lean]}`}>{lean}</span>
                  {a && <span>{a.n} 場 · {a.y0}–{a.y1}</span>}
                </div>
              </a>
            );
          })}
        </div>
      )}
    </section>
  );
}
