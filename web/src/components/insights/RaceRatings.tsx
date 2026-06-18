import type { RaceRating } from "../../lib/types";
import { raceHref } from "../../lib/race-url";

const stars = (n: number) => "★".repeat(n) + "☆".repeat(5 - n);

export default function RaceRatings({ ratings }: { ratings: RaceRating[] }) {
  if (!ratings.length) return <p className="text-muted">無資料</p>;
  return (
    <div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted">
              <th className="py-1 pr-3 num">#</th><th className="py-1 pr-3">星等</th>
              <th className="py-1 pr-3">賽事</th><th className="py-1 pr-3 num">中位人數</th>
              <th className="py-1 pr-3 num">屆數</th><th className="py-1 pr-3 num">常客%</th>
            </tr>
          </thead>
          <tbody>
            {ratings.slice(0, 40).map((r, i) => {
              const y = r.years[r.years.length - 1];
              return (
                <tr key={r.race_key} className="border-t border-border/60">
                  <td className="py-1.5 pr-3 num text-muted">{i + 1}</td>
                  <td className="py-1.5 pr-3 text-accent" title={`score ${r.score}`}>{stars(r.stars)}</td>
                  <td className="py-1.5 pr-3">
                    <a className="text-ink hover:text-accent"
                      href={raceHref(r.race_key, y)}>{r.name}</a>
                  </td>
                  <td className="py-1.5 pr-3 num text-muted">{r.med_field.toLocaleString()}</td>
                  <td className="py-1.5 pr-3 num text-muted">{r.editions}</td>
                  <td className="py-1.5 pr-3 num text-muted">{r.regular_pct}%</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-muted">
        星等 = 規模(中位完賽人數)+ 屆數(舉辦年數)+ 場域深度(常客佔比,常客=曾出賽 ≥3 場的選手)綜合評分,跨賽事排名分級。僅列中位完賽 ≥20 人的賽事。
      </p>
    </div>
  );
}
