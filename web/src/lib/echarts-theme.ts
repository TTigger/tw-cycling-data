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
  color: ["#D23120", "#3F6B78", "#5C7355", "#C98A1E", "#8A6D9C", "#A0564B"],
  backgroundColor: "transparent",
  animationDuration: 700, animationEasing: "cubicOut",
  textStyle: { fontFamily: "Spline Sans Mono, Hanken Grotesk, Noto Sans TC, system-ui, sans-serif", color: "#12181A" },
  title: { textStyle: { color: "#12181A", fontFamily: "Fraunces, Noto Serif TC, serif" } },
  categoryAxis: {
    axisLine: { lineStyle: { color: "#D2D8D3" } }, axisTick: { lineStyle: { color: "#D2D8D3" } },
    axisLabel: { color: "#5A6560", fontFamily: "Spline Sans Mono, monospace" }, splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false }, axisTick: { show: false },
    axisLabel: { color: "#5A6560", fontFamily: "Spline Sans Mono, monospace" },
    splitLine: { lineStyle: { color: "#D2D8D3", type: "dashed" } },
  },
  legend: { textStyle: { color: "#5A6560" } },
  // radar is its own coordinate system (not category/value axis) — theme it so
  // charts don't hard-code light colors that break in dark mode.
  radar: {
    axisName: { color: "#5A6560" }, splitArea: { show: false },
    axisLine: { lineStyle: { color: "#D2D8D3" } }, splitLine: { lineStyle: { color: "#D2D8D3" } },
  },
  tooltip: {
    backgroundColor: "#FFFFFF", borderColor: "#D2D8D3",
    textStyle: { color: "#12181A", fontFamily: "Spline Sans Mono, Hanken Grotesk, sans-serif" },
  },
});

// Dark variant — same warm palette, light text + darker grid for dark mode.
echarts.registerTheme("claude-dark", {
  color: ["#EC3A2B", "#7FA9B6", "#9BB089", "#F2B84B", "#B597BA", "#C2766A"],
  backgroundColor: "transparent",
  animationDuration: 700, animationEasing: "cubicOut",
  textStyle: { fontFamily: "Spline Sans Mono, Hanken Grotesk, Noto Sans TC, system-ui, sans-serif", color: "#ECEFEC" },
  title: { textStyle: { color: "#ECEFEC", fontFamily: "Fraunces, Noto Serif TC, serif" } },
  categoryAxis: {
    axisLine: { lineStyle: { color: "#2A3538" } }, axisTick: { lineStyle: { color: "#2A3538" } },
    axisLabel: { color: "#84908A", fontFamily: "Spline Sans Mono, monospace" }, splitLine: { show: false },
  },
  valueAxis: {
    axisLine: { show: false }, axisTick: { show: false },
    axisLabel: { color: "#84908A", fontFamily: "Spline Sans Mono, monospace" },
    splitLine: { lineStyle: { color: "#222B2E", type: "dashed" } },
  },
  legend: { textStyle: { color: "#84908A" } },
  radar: {
    axisName: { color: "#84908A" }, splitArea: { show: false },
    axisLine: { lineStyle: { color: "#2A3538" } }, splitLine: { lineStyle: { color: "#2A3538" } },
  },
  tooltip: {
    backgroundColor: "#161D20", borderColor: "#2A3538",
    textStyle: { color: "#ECEFEC", fontFamily: "Spline Sans Mono, Hanken Grotesk, sans-serif" },
  },
});

export { echarts };
export const CLAUDE_THEME = "claude";
