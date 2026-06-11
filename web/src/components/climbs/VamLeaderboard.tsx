import { useMemo } from "react";
import type { DetailRow, ClimbProfile } from "../../lib/types";
import { vam, wkgEstimate, isPlausibleVam } from "../../lib/vam";
import { secondsToHMS } from "../../lib/format";

export default function VamLeaderboard({ rows, profile }: { rows: DetailRow[]; profile: ClimbProfile }) {
  const ranked = useMemo(() => {
    const out = rows
      .map((r) => ({ r, v: vam(profile.elev_m, r.t) }))
      .filter((x) => isPlausibleVam(x.v))
      .sort((a, b) => (b.v as number) - (a.v as number));
    return out;
  }, [rows, profile]);

  const dropped = rows.filter((r) => r.t).length - ranked.length;

  return (
    <div>
      <p className="mb-2 text-xs text-muted">
        {profile.name} · {profile.dist_km}km · 爬升 {profile.elev_m}m · 均斜率 {profile.grade}%
        {profile.conf === "est" && " · 路線數據為估計"}({profile.src})
      </p>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-muted">
              <th className="py-1 pr-3 num">#</th><th className="py-1 pr-3">選手</th>
              <th className="py-1 pr-3 num">VAM</th><th className="py-1 pr-3 num">推算 W/kg</th>
              <th className="py-1 pr-3 num">完賽</th><th className="py-1 pr-3">車隊</th>
            </tr>
          </thead>
          <tbody>
            {ranked.slice(0, 50).map((x, i) => (
              <tr key={i} className="border-t border-border/60">
                <td className="py-1.5 pr-3 num text-muted">{i + 1}</td>
                <td className="py-1.5 pr-3 text-ink">{x.r.name ?? "—"}</td>
                <td className="py-1.5 pr-3 num text-accent">{x.v}</td>
                <td className="py-1.5 pr-3 num text-muted">{wkgEstimate(x.v, profile.grade) ?? "—"}</td>
                <td className="py-1.5 pr-3 num text-muted">{secondsToHMS(x.r.t)}</td>
                <td className="py-1.5 pr-3 text-muted">{x.r.team ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {dropped > 0 && <p className="mt-2 text-xs text-muted">已濾除 {dropped} 筆時間異常(VAM 超出合理範圍)。</p>}
    </div>
  );
}
