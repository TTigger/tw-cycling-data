import ReactEChartsCore from "echarts-for-react/lib/core";
import type { EChartsOption } from "echarts";
import { echarts, CLAUDE_THEME } from "../../lib/echarts-theme";
import { useDark } from "../../lib/chart-colors";

interface Props {
  option: EChartsOption;
  height?: number;
  onEvents?: Record<string, (params: any) => void>;
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
