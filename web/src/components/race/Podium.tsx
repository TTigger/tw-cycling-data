import { podium } from "../../lib/racedetail";
import { secondsToHMS } from "../../lib/format";
import type { DetailRow } from "../../lib/types";

const MEDAL = ["#D9A441", "#9FA6AD", "#B07A52"];

export default function Podium({ rows }: { rows: DetailRow[] }) {
  const top = podium(rows, 3);
  if (!top.length) return <p className="text-muted">無名次資料</p>;
  return (
    <div className="flex flex-wrap gap-3">
      {top.map((p, i) => (
        <div key={i} className="min-w-[140px] flex-1 rounded-xl border border-border bg-surface p-3">
          <div className="num text-lg" style={{ color: MEDAL[i] }}>#{p.rank}</div>
          <div className="text-ink">{p.name ?? "—"}</div>
          <div className="text-xs text-muted">{p.team ?? ""}</div>
          <div className="num text-sm text-muted">{secondsToHMS(p.t)}</div>
        </div>
      ))}
    </div>
  );
}
