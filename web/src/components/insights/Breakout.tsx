import type { BreakoutEntry } from "../../lib/types";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

export default function Breakout({ entries }: { entries: BreakoutEntry[] }) {
  if (!entries.length) return <p className="text-muted">無資料</p>;
  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted">
              <th className="py-1 pr-3 num">#</th><th className="py-1 pr-3">選手</th>
              <th className="py-1 pr-3 num">躍升</th><th className="py-1 pr-3">前→後(贏過全場%)</th>
              <th className="py-1 pr-3">年度</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => (
              <tr key={e.id} className="border-t border-border/60">
                <td className="py-1.5 pr-3 num text-muted">{i + 1}</td>
                <td className="py-1.5 pr-3">
                  <a className="text-ink hover:text-accent" href={`${base}/athletes?id=${e.id}`}>{e.nm}</a>
                  {e.anchored && <span className="ml-1 text-xs text-emerald-600 dark:text-emerald-400" title="以 TCU/UCI 選手編號歸併,身分可靠">★</span>}
                </td>
                <td className="py-1.5 pr-3 num text-accent">+{e.jump}</td>
                <td className="py-1.5 pr-3 num text-muted">{e.from_pct}% → {e.to_pct}%</td>
                <td className="py-1.5 pr-3 num text-muted">{e.from_y}→{e.to_y}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-muted">
        躍升 = 相鄰參賽年度「贏過全場 %」中位數的最大增幅(每年至少 2 場)。
        ★ 為以 TCU/UCI 選手編號歸併的可靠身分;其餘以姓名歸併,可能含同名,僅供參考。
      </p>
    </div>
  );
}
