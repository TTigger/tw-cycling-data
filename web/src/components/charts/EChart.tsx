import ReactECharts from "echarts-for-react";
import type { EChartsOption } from "echarts";
import { CLAUDE_THEME } from "../../lib/echarts-theme";

interface Props {
  option: EChartsOption;
  height?: number;
  onEvents?: Record<string, (params: any) => void>;
}

export default function EChart({ option, height = 320, onEvents }: Props) {
  return (
    <ReactECharts
      option={option}
      theme={CLAUDE_THEME}
      notMerge
      lazyUpdate
      style={{ height, width: "100%" }}
      onEvents={onEvents}
    />
  );
}
