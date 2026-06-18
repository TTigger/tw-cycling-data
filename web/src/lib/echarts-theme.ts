// Tree-shaken ECharts: pull in only the chart types + components actually used
// across the dashboard, instead of the ~1.1MB full barrel. Importing this module
// (for side-effect or via EChart) registers them and the "claude" theme once.
import * as echarts from "echarts/core";
import { LineChart, BarChart, ScatterChart, BoxplotChart, HeatmapChart, RadarChart } from "echarts/charts";
import {
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  VisualMapComponent, AxisPointerComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([
  // series used: line, bar, scatter, boxplot, heatmap, radar
  LineChart, BarChart, ScatterChart, BoxplotChart, HeatmapChart, RadarChart,
  // option blocks used: grid, tooltip, legend, title, visualMap, axisPointer
  GridComponent, TooltipComponent, LegendComponent, TitleComponent,
  VisualMapComponent, AxisPointerComponent,
  CanvasRenderer,
]);

// Claude warm palette, registered once and referenced by name "claude".
echarts.registerTheme("claude", {
  color: ["#D97757", "#5B7B8A", "#7C8C6B", "#C99A6B", "#9A7AA0", "#A0564B"],
  backgroundColor: "transparent",
  animationDuration: 700, animationEasing: "cubicOut",
  textStyle: { fontFamily: "Hanken Grotesk, Noto Sans TC, system-ui, sans-serif", color: "#1F1E1D" },
  title: { textStyle: { color: "#1F1E1D", fontFamily: "Fraunces, Noto Serif TC, serif" } },
  categoryAxis: {
    axisLine: { lineStyle: { color: "#E8E3D9" } }, axisTick: { lineStyle: { color: "#E8E3D9" } },
    axisLabel: { color: "#6B6760" }, splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: "#6B6760" },
    splitLine: { lineStyle: { color: "#E8E3D9", type: "dashed" } },
  },
  legend: { textStyle: { color: "#6B6760" } },
  // radar is its own coordinate system (not category/value axis) — theme it so
  // charts don't hard-code light colors that break in dark mode.
  radar: {
    axisName: { color: "#6B6760" }, splitArea: { show: false },
    axisLine: { lineStyle: { color: "#E8E3D9" } }, splitLine: { lineStyle: { color: "#E8E3D9" } },
  },
  tooltip: {
    backgroundColor: "#FFFFFF", borderColor: "#E8E3D9",
    textStyle: { color: "#1F1E1D", fontFamily: "Hanken Grotesk, Noto Sans TC, sans-serif" },
  },
});

// Dark variant — same warm palette, light text + darker grid for dark mode.
echarts.registerTheme("claude-dark", {
  color: ["#E8916F", "#7FA0B0", "#9BAE89", "#D6B083", "#B597BA", "#C2766A"],
  backgroundColor: "transparent",
  animationDuration: 700, animationEasing: "cubicOut",
  textStyle: { fontFamily: "Hanken Grotesk, Noto Sans TC, system-ui, sans-serif", color: "#ECE9E3" },
  title: { textStyle: { color: "#ECE9E3", fontFamily: "Fraunces, Noto Serif TC, serif" } },
  categoryAxis: {
    axisLine: { lineStyle: { color: "#34303A" } }, axisTick: { lineStyle: { color: "#34303A" } },
    axisLabel: { color: "#9C968C" }, splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: "#9C968C" },
    splitLine: { lineStyle: { color: "#2C2932", type: "dashed" } },
  },
  legend: { textStyle: { color: "#9C968C" } },
  radar: {
    axisName: { color: "#9C968C" }, splitArea: { show: false },
    axisLine: { lineStyle: { color: "#34303A" } }, splitLine: { lineStyle: { color: "#34303A" } },
  },
  tooltip: {
    backgroundColor: "#211F24", borderColor: "#34303A",
    textStyle: { color: "#ECE9E3", fontFamily: "Hanken Grotesk, Noto Sans TC, sans-serif" },
  },
});

export { echarts };
export const CLAUDE_THEME = "claude";
