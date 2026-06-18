import type { Records, RecordAthlete } from "../../lib/types";
import { raceHref } from "../../lib/race-url";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");
const MEDAL = ["🥇", "🥈", "🥉"];

interface Row { key: string; href: string; label: string; value: string; }

function Board({ title, hint, rows }: { title: string; hint: string; rows: Row[] }) {
  return (
    <div className="rounded-lg border border-border bg-bg p-3">
      <h3 className="text-sm text-ink">{title}</h3>
      <p className="mb-2 text-xs text-muted">{hint}</p>
      <ol className="space-y-1">
        {rows.map((r, i) => (
          <li key={r.key} className="flex items-center gap-2 text-sm">
            <span className="w-5 shrink-0 text-center text-xs">{MEDAL[i] ?? i + 1}</span>
            <a href={r.href} className="min-w-0 flex-1 truncate text-ink hover:text-accent">{r.label}</a>
            <span className="num shrink-0 text-accent">{r.value}</span>
          </li>
        ))}
      </ol>
    </div>
  );
}

export default function RecordsWall({ records }: { records: Records }) {
  const ath = (rows: RecordAthlete[], unit: string): Row[] =>
    rows.map((r) => ({ key: r.id, href: `${base}/athletes?id=${r.id}`, label: r.nm, value: `${r.v}${unit}` }));

  const boards = [
    {
      title: "最大場面", hint: "單場(年)完賽人數",
      rows: records.biggest_field.map((r) => ({
        key: `${r.rk}-${r.y}`, href: raceHref(r.rk, r.y),
        label: `${r.y} ${r.name}`, value: `${r.n.toLocaleString()} 人`,
      })),
    },
    { title: "生涯最多出賽", hint: "完賽場次最多", rows: ath(records.most_starts, " 場") },
    { title: "生涯最多冠軍", hint: "第一名次數", rows: ath(records.most_wins, " 冠") },
    { title: "跨最多賽事", hint: "出賽過的不同賽事數", rows: ath(records.most_races, " 賽") },
    { title: "最長連續參賽", hint: "連續出賽年數", rows: ath(records.longest_streak, " 年") },
    {
      title: "❤️ 同場回頭王", hint: "同一賽事參賽最多年",
      rows: records.most_loyal.map((r) => ({
        key: r.id, href: `${base}/athletes?id=${r.id}`,
        label: `${r.nm}・${r.name}`, value: `${r.v} 年`,
      })),
    },
  ];

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {boards.map((b) => <Board key={b.title} {...b} />)}
    </div>
  );
}
