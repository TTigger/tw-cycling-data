import { useEffect, useState } from "react";
import { loadManifest, fetchEndpoint } from "../../lib/data-load";
import { isTemplated, endpointPreview, curlExample, pythonExample } from "../../lib/api-explorer";
import type { Manifest, ManifestEndpoint } from "../../lib/types";
import Skeleton from "../Skeleton";

const BASE = "https://tw-cycling-data.vercel.app/data/v1";
const GH = "https://github.com/TTigger/tw-cycling-data";

function CopyButton({ text }: { text: string }) {
  const [done, setDone] = useState(false);
  return (
    <button type="button"
      onClick={() => { navigator.clipboard?.writeText(text); setDone(true); setTimeout(() => setDone(false), 1200); }}
      className="rounded border border-border px-2 py-0.5 text-xs text-muted hover:text-accent">
      {done ? "已複製" : "複製"}
    </button>
  );
}

function EndpointRow({ ep }: { ep: ManifestEndpoint }) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const [preview, setPreview] = useState<{ summary: string; body: string } | null>(null);
  const templated = isTemplated(ep.path);

  const onPreview = async () => {
    if (open) { setOpen(false); return; }
    setOpen(true); setState("loading"); setPreview(null);
    try {
      const data = await fetchEndpoint(ep.path);
      setPreview(endpointPreview(data));
      setState("idle");
    } catch {
      setState("error");
    }
  };

  return (
    <>
      <tr className="border-t border-border align-top">
        <td className="py-2 pr-3"><code className="text-accent">{ep.path}</code></td>
        <td className="py-2 pr-3 text-xs text-muted">{ep.kind}</td>
        <td className="py-2 pr-3">{ep.description}</td>
        <td className="py-2 whitespace-nowrap">
          {templated ? (
            <span className="text-xs text-muted">
              需 id(見 {" "}
              <a className="hover:text-accent" href={`${BASE}/races.json`} target="_blank" rel="noopener">races.json</a>{" / "}
              <a className="hover:text-accent" href={`${BASE}/athletes.json`} target="_blank" rel="noopener">athletes.json</a>{" / "}
              <a className="hover:text-accent" href={`${BASE}/teams.json`} target="_blank" rel="noopener">teams.json</a>)
            </span>
          ) : (
            <span className="flex gap-2">
              <button type="button" onClick={onPreview}
                className="rounded border border-border px-2 py-0.5 text-xs hover:text-accent">
                {open ? "收合" : "預覽"}
              </button>
              <a href={`${BASE}/${ep.path}`} target="_blank" rel="noopener"
                className="text-xs text-muted hover:text-accent">開新分頁↗</a>
            </span>
          )}
        </td>
      </tr>
      {open && (
        <tr className="border-t border-border/50">
          <td colSpan={4} className="py-2">
            {state === "loading" && <p className="text-xs text-muted">載入中…</p>}
            {state === "error" && <p className="text-xs text-accent">載入失敗,請稍後再試。</p>}
            {preview && (
              <div className="space-y-1">
                <p className="text-xs text-muted">{preview.summary}</p>
                <pre className="overflow-auto rounded bg-surface p-2 text-xs">{preview.body}</pre>
              </div>
            )}
          </td>
        </tr>
      )}
    </>
  );
}

export default function ApiExplorer() {
  const [m, setM] = useState<Manifest | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    loadManifest().then(setM).catch(() => setFailed(true));
  }, []);

  if (failed) return <p className="text-accent">無法載入 API manifest,請稍後再試。</p>;
  if (!m) return <Skeleton cards={2} />;

  const s = m.stats;
  const stat = (label: string, v: number | string) => (
    <div className="rounded-lg border border-border bg-surface px-3 py-2">
      <div className="num text-lg text-ink">{v}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );

  return (
    <div className="space-y-6 text-sm">
      <section className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {stat("筆數", s.records.toLocaleString())}
        {stat("賽事", s.races)}
        {stat("賽事屆數", s.race_editions)}
        {stat("選手", s.athletes.toLocaleString())}
        {stat("車隊", s.teams.toLocaleString())}
        {stat("來源", s.sources)}
        {stat("年份", `${s.year_min}–${s.year_max}`)}
        {stat("授權", m.license)}
      </section>

      <section>
        <h2 className="font-display text-xl">端點</h2>
        <p className="mb-2 text-xs text-muted">Base:<code>{BASE}</code>。皆唯讀 JSON,帶 CORS,可直接跨網域 fetch。</p>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead><tr className="text-xs text-muted">
              <th className="py-1 pr-3">路徑</th><th className="py-1 pr-3">類型</th>
              <th className="py-1 pr-3">說明</th><th className="py-1"></th>
            </tr></thead>
            <tbody>{m.endpoints.map((ep) => <EndpointRow key={ep.path} ep={ep} />)}</tbody>
          </table>
        </div>
      </section>

      <section>
        <h2 className="font-display text-xl">複製即用</h2>
        <div className="space-y-2">
          <div className="flex items-center gap-2"><span className="text-xs text-muted">curl</span>
            <CopyButton text={curlExample(BASE, "races.json")} /></div>
          <pre className="overflow-auto rounded bg-surface p-2 text-xs">{curlExample(BASE, "races.json")}</pre>
          <div className="flex items-center gap-2"><span className="text-xs text-muted">Python</span>
            <CopyButton text={pythonExample(BASE, "races.json")} /></div>
          <pre className="overflow-auto rounded bg-surface p-2 text-xs">{pythonExample(BASE, "races.json")}</pre>
        </div>
      </section>

      <section className="text-xs text-muted">
        延伸:<a className="hover:text-accent" href={`${GH}/blob/master/docs/API.md`}>完整 API 文件</a>・
        <a className="hover:text-accent" href={`${GH}/tree/master/mcp-server`}>MCP server</a>・
        <a className="hover:text-accent" href={`${GH}/releases`}>開放資料集(Releases)</a>・
        授權 {m.license}({m.attribution})。
      </section>
    </div>
  );
}
