import { useEffect, useState } from "react";
import ReactEChartsCore from "echarts-for-react/lib/core";
import type { EChartsOption } from "echarts";
import { echarts, CLAUDE_THEME } from "../../lib/echarts-theme";

interface Props {
  option: EChartsOption;
  height?: number;
  onEvents?: Record<string, (params: any) => void>;
}

/** Follows the site theme: re-mounts with the dark chart theme on toggle. */
function useDark(): boolean {
  const [dark, setDark] = useState(
    () => typeof document !== "undefined" && document.documentElement.classList.contains("dark"),
  );
  useEffect(() => {
    const on = () => setDark(document.documentElement.classList.contains("dark"));
    window.addEventListener("themechange", on);
    return () => window.removeEventListener("themechange", on);
  }, []);
  return dark;
}

export default function EChart({ option, height = 320, onEvents }: Props) {
  const theme = useDark() ? "claude-dark" : CLAUDE_THEME;
  return (
    <ReactEChartsCore
      key={theme}
      echarts={echarts}
      option={option}
      theme={theme}
      notMerge
      lazyUpdate
      style={{ height, width: "100%" }}
      onEvents={onEvents}
    />
  );
}
