import { useEffect, useMemo, useState } from "react";
import type { EChartsOption } from "echarts";
import EChart from "../charts/EChart";
import { loadRaceDna } from "../../lib/data-load";
import { DNA_AXES, dnaFor, dnaRadarValues, dnaRaceList, similarRaces } from "../../lib/race-dna";
import type { RaceDnaFile } from "../../lib/types";

const base = import.meta.env.BASE_URL.replace(/\/$/, "");

export default function RaceDna(
  { rk, year, name }: { rk: string; year: number | null; name: string },
) {
  const [file, setFile] = useState<RaceDnaFile | null>(null);
  const [err, setErr] = useState(false);
  const [cmp, setCmp] = useState<string>(""); // index into `options` of the compare pick

  useEffect(() => {
    let live = true;
    loadRaceDna()
      .then((f) => { if (live) setFile(f); })
      .catch(() => { if (live) setErr(true); });
    return () => { live = false; };
  }, []);

  useEffect(() => { setCmp(""); }, [rk, year]); // reset compare when the race changes

  const primary = file ? dnaFor(file, rk, year) : null;
  const options = useMemo(() => (file ? dnaRaceList(file) : []), [file]);
  const cmpOpt = cmp !== "" ? options[Number(cmp)] : null;
  const compare = file && cmpOpt ? dnaFor(file, cmpOpt.rk, cmpOpt.year) : null;
  const cmpName = cmpOpt?.label ?? "";
  const similar = useMemo(
    () => (file ? similarRaces(file, rk, year, 5) : []),
    [file, rk, year],
  );

  if (err) return null;
  if (!file) return <p className="text-sm text-muted">計算中…</p>;
  if (!primary)
    return <p className="text-sm text-muted">此場完賽人數不足(&lt;20),未產生 DNA 指紋。</p>;

  const series = [{ name: `${year} ${name}`, value: dnaRadarValues(primary) }];
  if (compare) series.push({ name: cmpName, value: dnaRadarValues(compare) });

  const option: EChartsOption = {
    radar: {
      indicator: DNA_AXES.map((a) => ({ name: a.label, max: 100 })),
      radius: "62%", axisName: { fontSize: 11 },
      splitArea: { areaStyle: { color: ["rgba(0,0,0,0)", "rgba(217,119,87,0.04)"] } },
    },
    legend: { bottom: 0, data: series.map((s) => s.name) },
    tooltip: {
      trigger: "item",
      formatter: (p: any) =>
        `${p.name}<br/>` +
        DNA_AXES.map((a, i) => `${a.label}:${p.value[i]}`).join("<br/>"),
    },
    color: ["#D97757", "#5B7B8A"],
    series: [{
      type: "radar", data: series,
      areaStyle: { opacity: 0.12 }, lineStyle: { width: 2 },
    }],
  };

  return (
    <div>
      <div className="mb-3 flex flex-wrap items-center gap-2 text-sm">
        <span className="text-muted">並排比較:</span>
        <select value={cmp} onChange={(e) => setCmp(e.target.value)}
          className="max-w-[16rem] rounded-lg border border-border bg-bg px-2 py-1 text-sm text-ink outline-none focus:border-accent">
          <option value="">(選一場賽事)</option>
          {options.map((o, i) => (
            <option key={`${o.rk}-${o.year}`} value={String(i)}>{o.label}</option>
          ))}
        </select>
        {compare && (
          <button onClick={() => setCmp("")} className="text-xs text-muted hover:text-accent">清除</button>
        )}
      </div>
      <EChart option={option} height={320} />
      <p className="mt-2 text-xs text-muted">
        六軸皆跨全站正規化為 0–100(該場在所有賽事年中的相對位置):
        {DNA_AXES.map((a) => `${a.label}=${a.hint}`).join("、")}。僅供參考。
      </p>

      {similar.length > 0 && (
        <div className="mt-4 border-t border-border/60 pt-3">
          <h3 className="text-sm text-ink">🧭 DNA 最相似的賽事</h3>
          <p className="mb-2 text-xs text-muted">六軸指紋最接近的其他賽事(不含本賽事其他屆),點擊前往。</p>
          <div className="flex flex-wrap gap-2">
            {similar.map((s) => (
              <a key={`${s.rk}-${s.year}`}
                href={`${base}/race?rk=${encodeURIComponent(s.rk)}&y=${s.year}`}
                className="rounded-lg border border-border bg-bg px-3 py-2 text-sm hover:border-accent">
                <span className="text-ink">{s.year} {s.name}</span>
                <span className="ml-2 num text-accent">{s.sim}%</span>
              </a>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
