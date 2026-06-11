import ReactEChartsCore from "echarts-for-react/lib/core";
import type { EChartsOption } from "echarts";
import { echarts, CLAUDE_THEME } from "../../lib/echarts-theme";

interface Props {
  option: EChartsOption;
  height?: number;
  onEvents?: Record<string, (params: any) => void>;
}

export default function EChart({ option, height = 320, onEvents }: Props) {
  return (
    <ReactEChartsCore
      echarts={echarts}
      option={option}
      theme={CLAUDE_THEME}
      notMerge
      lazyUpdate
      style={{ height, width: "100%" }}
      onEvents={onEvents}
    />
  );
}
