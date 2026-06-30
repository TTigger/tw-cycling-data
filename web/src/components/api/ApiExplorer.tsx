import { useEffect, useState } from "react";
import { loadManifest, fetchEndpoint } from "../../lib/data-load";
import { isTemplated, endpointPreview, curlExample, pythonExample, jsExample } from "../../lib/api-explorer";
import type { Manifest, ManifestEndpoint } from "../../lib/types";
import Skeleton from "../Skeleton";

const BASE = "https://tw-cycling-data.vercel.app/data/v1";
const GH = "https://github.com/TTigger/tw-cycling-data";

function CopyButton({ text, label = "複製" }: { text: string; label?: string }) {
  const [done, setDone] = useState(false);
  return (
    <button type="button" aria-label={label} title={label}
      onClick={async () => { try { await navigator.clipboard?.writeText(text); } catch { return; } setDone(true); setTimeout(() => setDone(false), 1200); }}
      className="rounded border border-border p-1 text-muted hover:text-accent">
      {done ? (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden="true"><path d="M20 6 9 17l-5-5" /></svg>
      ) : (
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true"><rect x="9" y="9" width="11" height="11" rx="2" /><path d="M5 15V5a2 2 0 0 1 2-2h10" /></svg>
      )}
    </button>
  );
}

function Snippet({ label, code }: { label: string; code: string }) {
  return (
    <div>
      <div className="flex items-center gap-2">
        <span className="text-xs font-medium text-muted">{label}</span>
        <CopyButton text={code} label={`複製 ${label}`} />
      </div>
      <pre className="mt-1 overflow-auto rounded bg-surface p-2 text-xs">{code}</pre>
    </div>
  );
}

function EndpointRow({ ep }: { ep: ManifestEndpoint }) {
  const [open, setOpen] = useState(false);
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const [preview, setPreview] = useState<{ summary: string; body: string } | null>(null);
  const templated = isTemplated(ep.path);

  const onPreview = async () => {
    setState("loading"); setPreview(null);
    try { setPreview(endpointPreview(await fetchEndpoint(ep.path))); setState("idle"); }
    catch { setState("error"); }
  };

  return (
    <>
      <tr className="border-t border-border align-top">
        <td className="py-2 pr-3"><code className="text-accent">{ep.path}</code></td>
        <td className="py-2 pr-3 text-xs text-muted">{ep.kind}</td>
        <td className="py-2 pr-3">{ep.description}</td>
        <td className="py-2 whitespace-nowrap">
          <button type="button"
            onClick={() => { if (open) { setState("idle"); setPreview(null); } setOpen((o) => !o); }}
            className="rounded border border-border px-2 py-0.5 text-xs hover:text-accent">
            {open ? "收合" : "範例"}
          </button>
        </td>
      </tr>
      {open && (
        <tr className="border-t border-border/50">
          <td colSpan={4} className="py-3">
            <div className="space-y-2">
              <Snippet label="curl" code={curlExample(BASE, ep.path)} />
              <Snippet label="Python" code={pythonExample(BASE, ep.path)} />
              <Snippet label="JS" code={jsExample(BASE, ep.path)} />
              {templated ? (
                <p className="text-xs text-muted">
                  路徑含 <code>{"{…}"}</code> 佔位,需 id —— 見{" "}
                  <a className="hover:text-accent" href={`${BASE}/races.json`} target="_blank" rel="noopener noreferrer">races.json</a>{" / "}
                  <a className="hover:text-accent" href={`${BASE}/athletes.json`} target="_blank" rel="noopener noreferrer">athletes.json</a>{" / "}
                  <a className="hover:text-accent" href={`${BASE}/teams.json`} target="_blank" rel="noopener noreferrer">teams.json</a>。
                </p>
              ) : (
                <div className="space-y-1">
                  <div className="flex items-center gap-3">
                    <button type="button" onClick={onPreview}
                      className="rounded border border-border px-2 py-0.5 text-xs hover:text-accent">即時預覽</button>
                    <a href={`${BASE}/${ep.path}`} target="_blank" rel="noopener noreferrer"
                      className="text-xs text-muted hover:text-accent">開新分頁↗</a>
                  </div>
                  {state === "loading" && <p className="text-xs text-muted">載入中…</p>}
                  {state === "error" && <p className="text-xs text-accent">載入失敗,請稍後再試。</p>}
                  {preview && (
                    <div className="space-y-1">
                      <p className="text-xs text-muted">{preview.summary}</p>
                      <pre className="overflow-auto rounded bg-surface p-2 text-xs">{preview.body}</pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

export default function ApiExplorer() {
  const [m, setM] = useState<Manifest | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => { loadManifest().then(setM).catch(() => setFailed(true)); }, []);

  if (failed) return <p className="text-accent">無法載入 API manifest,請稍後再試。</p>;
  if (!m) return <Skeleton cards={2} />;

  const s = m.stats;
  const heroSnippet = jsExample(BASE, "races.json");
  const badge = (label: string, v: number | string) => (
    <span className="rounded-full border border-border bg-surface px-2.5 py-1 text-xs">
      <span className="num text-ink">{v}</span> <span className="text-muted">{label}</span>
    </span>
  );

  return (
    <div className="space-y-6 text-sm">
      <section className="space-y-3">
        <p className="text-muted">唯讀 JSON API;帶 CORS,可直接跨網域 fetch。去識別化,CC BY 4.0。</p>
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs text-muted">Base URL</span>
          <code className="rounded bg-surface px-2 py-1 text-xs text-accent">{BASE}</code>
          <CopyButton text={BASE} label="複製 Base URL" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-muted">10 秒上手</span>
            <CopyButton text={heroSnippet} label="複製範例" />
          </div>
          <pre className="mt-1 overflow-auto rounded bg-surface p-2 text-xs">{heroSnippet}</pre>
        </div>
      </section>

      <section className="flex flex-wrap gap-2">
        {badge("筆數", s.records.toLocaleString())}
        {badge("賽事", s.races)}
        {badge("屆數", s.race_editions)}
        {badge("選手", s.athletes.toLocaleString())}
        {badge("車隊", s.teams.toLocaleString())}
        {badge("來源", s.sources)}
        {badge("年份", `${s.year_min}–${s.year_max}`)}
        {badge("授權", m.license)}
      </section>

      <section>
        <h2 className="font-display text-xl">端點</h2>
        <p className="mb-2 text-xs text-muted">點「範例」看該端點的 curl / Python / JS 與即時預覽。Base:<code>{BASE}</code></p>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead><tr className="text-xs text-muted">
              <th className="py-1 pr-3">路徑</th><th className="py-1 pr-3">類型</th>
              <th className="py-1 pr-3">說明</th><th className="py-1">範例</th>
            </tr></thead>
            <tbody>{m.endpoints.map((ep) => <EndpointRow key={ep.path} ep={ep} />)}</tbody>
          </table>
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
