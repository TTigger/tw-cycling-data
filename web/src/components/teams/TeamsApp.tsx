import { useEffect, useMemo, useState } from "react";
import { loadTeams, loadTeam } from "../../lib/data-load";
import type { TeamIndexEntry, TeamDetail } from "../../lib/types";
import TeamProfile from "./TeamProfile";
import Skeleton from "../Skeleton";

const SHOW = 60;

function searchTeams(list: TeamIndexEntry[], q: string): TeamIndexEntry[] {
  const s = q.trim().toLowerCase();
  if (!s) return list.slice(0, SHOW);
  return list.filter((t) => t.name.toLowerCase().includes(s)).slice(0, SHOW);
}

export default function TeamsApp() {
  const [list, setList] = useState<TeamIndexEntry[]>([]);
  const [q, setQ] = useState("");
  const [sel, setSel] = useState<TeamDetail | null>(null);
  const [loadingSel, setLoadingSel] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    loadTeams().then((l) => {
      setList(l);
      const id = new URLSearchParams(location.search).get("id");
      if (id) pick(id, false);
    }).catch((e) => setErr(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // keep the view in sync with the browser back/forward buttons.
  useEffect(() => {
    if (!list.length) return;
    const onPop = () => {
      const id = new URLSearchParams(location.search).get("id");
      if (id) { if (!sel || sel.id !== id) pick(id, false); }
      else setSel(null);
    };
    window.addEventListener("popstate", onPop);
    return () => window.removeEventListener("popstate", onPop);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [list, sel]);

  function pick(id: string, pushUrl = true) {
    setLoadingSel(true); setSel(null);
    if (pushUrl) history.pushState(null, "", `?id=${id}`);
    loadTeam(id).then((d) => { setSel(d); setLoadingSel(false); })
      .catch((e) => { setErr(String(e)); setLoadingSel(false); });
  }
  function back() {
    setSel(null);
    history.pushState(null, "", location.pathname);
  }

  const results = useMemo(() => searchTeams(list, q), [list, q]);

  if (err) return <p className="text-accent">資料載入失敗:{err}</p>;
  if (!list.length) return <Skeleton cards={3} />;
  if (sel) return <TeamProfile d={sel} onBack={back} />;
  if (loadingSel) return <Skeleton cards={2} />;

  return (
    <div className="space-y-5">
      <input
        value={q} onChange={(e) => setQ(e.target.value)}
        placeholder="搜尋車隊,例如「崇越」或「RCC」"
        className="w-full max-w-md rounded-lg border border-border bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-accent"
      />
      <p className="text-xs text-muted">
        共 {list.length.toLocaleString()} 支車隊(≥4 位可追蹤車手)。顯示前 {results.length} 筆;依車手人數排序。
      </p>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {results.map((t) => (
          <button key={t.id} onClick={() => pick(t.id)}
            className="rounded-xl border border-border bg-surface p-3 text-left hover:border-accent">
            <div className="font-display text-ink">{t.name}</div>
            <div className="mt-1 text-xs text-muted">
              {t.riders} 位車手 · {t.races} 賽事 · {t.y0}–{t.y1}
            </div>
            <div className="mt-1 text-xs text-muted">
              {t.wins} 冠軍 · {t.podiums} 前三
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
