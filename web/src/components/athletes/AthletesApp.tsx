import { useEffect, useMemo, useState } from "react";
import "../../lib/echarts-theme";
import { loadAthletes, loadAthlete } from "../../lib/data-load";
import { searchAthletes, CONF_LABEL } from "../../lib/athletes";
import type { AthleteIndexEntry, AthleteDetail } from "../../lib/types";
import AthleteProfile from "./AthleteProfile";
import AthleteCompare from "./AthleteCompare";
import Skeleton from "../Skeleton";

const CONF_DOT: Record<string, string> = {
  high: "bg-emerald-400/70", med: "bg-amber-400/80", low: "bg-accent",
};

export default function AthletesApp({ initId }: { initId?: string } = {}) {
  const [list, setList] = useState<AthleteIndexEntry[]>([]);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<AthleteDetail | null>(null);
  const [cmp, setCmp] = useState<AthleteDetail | null>(null);
  const [loadingSel, setLoadingSel] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const p = new URLSearchParams(location.search);
    // top-N popular riders are SSG'd at /athletes/<id> (id via props); the
    // rest stay on the query-param SPA (/athletes?id=).
    const id = initId ?? p.get("id"), vs = p.get("vs");
    // Load the selected athlete's detail immediately — don't block it behind the
    // 2.6MB index. On a deep-linked profile the index is only needed for search /
    // compare / doppelganger, so defer it off the critical path; on the list view
    // (no id) it's the content, so load it now.
    if (id) pick(id, false);
    if (id && vs) loadAthlete(vs).then(setCmp).catch((e) => setErr(String(e)));
    const loadIdx = () => loadAthletes().then(setList).catch((e) => setErr(String(e)));
    if (id && typeof requestIdleCallback !== "undefined") requestIdleCallback(loadIdx, { timeout: 4000 });
    else loadIdx();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // keep the view in sync with the browser back/forward buttons.
  useEffect(() => {
    if (!list.length) return;
    const onPop = () => {
      const p = new URLSearchParams(location.search);
      const id = initId ?? p.get("id"), vs = p.get("vs");
      if (id) {
        if (!sel || sel.id !== id) pick(id, false);
        if (vs) { if (!cmp || cmp.id !== vs) loadAthlete(vs).then(setCmp).catch((e) => setErr(String(e))); }
        else setCmp(null);
      } else { setSel(null); setCmp(null); }
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [list, sel, cmp, initId]);

  function pick(id: string, pushUrl = true) {
    setLoadingSel(true); setSel(null); setCmp(null);
    if (pushUrl) history.pushState(null, "", `?id=${id}`);
    loadAthlete(id).then((d) => { setSel(d); setLoadingSel(false); })
      .catch((e) => { setErr(String(e)); setLoadingSel(false); });
  }

  function pickCompare(id: string) {
    const params = new URLSearchParams(location.search);
    params.set("vs", id);
    history.pushState(null, "", `?${params}`);
    setCmp(null);
    loadAthlete(id).then(setCmp).catch((e) => setErr(String(e)));
  }

  function clearCompare() {
    setCmp(null);
    const params = new URLSearchParams(location.search);
    params.delete("vs");
    history.pushState(null, "", `?${params}`);
  }

  function back() {
    setSel(null); setCmp(null);
    history.pushState(null, "", location.pathname);
  }

  const results = useMemo(() => searchAthletes(list, q), [list, q]);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!list.length) return <Skeleton cards={3} />;

  if (sel && cmp) return <AthleteCompare a={sel} b={cmp} onBack={clearCompare} />;
  if (sel) return <AthleteProfile d={sel} index={list} onBack={back} onCompare={pickCompare} />;
  if (loadingSel) return <Skeleton cards={2} />;

  return (
    <div className="space-y-5">
      <input
        value={q} onChange={(e) => setQ(e.target.value)}
        placeholder="搜尋遮罩姓名,例如「王○明」或「王」"
        className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent"
      />
      <p className="text-xs text-muted">
        共 {list.length.toLocaleString()} 位可追蹤選手(出賽 ≥2 場)。顯示前 {results.length} 筆;姓名已去識別化(保留首尾),身分以姓名+車隊+UCI 推斷。
      </p>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {results.map((a) => (
          <button key={a.id} onClick={() => pick(a.id)}
            className="rounded-xl border border-border bg-surface p-3 text-left hover:border-accent">
            <div className="flex items-center justify-between">
              <span className="font-display text-base text-ink">{a.nm}</span>
              <span className={`h-2 w-2 rounded-full ${CONF_DOT[a.conf]}`} title={CONF_LABEL[a.conf]} />
            </div>
            <div className="mt-1 text-xs text-muted">
              {a.y0}–{a.y1} · {a.n} 場 · {a.nr} 賽事{a.best ? ` · 最佳第 ${a.best}` : ""}
              {a.rid && " · TCU"}{a.uci && " · UCI"}
            </div>
          </button>
        ))}
        {!results.length && <p className="text-muted">查無符合的選手。</p>}
      </div>
    </div>
  );
}
