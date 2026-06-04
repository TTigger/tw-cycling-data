import { useEffect, useState } from "react";
import { loadViz } from "../lib/data-load";

export default function DataSmoke() {
  const [n, setN] = useState<number | null>(null);
  const [err, setErr] = useState<string | null>(null);
  useEffect(() => {
    loadViz().then((rows) => setN(rows.length)).catch((e) => setErr(String(e)));
  }, []);
  if (err) return <span className="text-accent">載入失敗:{err}</span>;
  return <span className="num">{n == null ? "載入中…" : `${n.toLocaleString()} 筆`}</span>;
}
