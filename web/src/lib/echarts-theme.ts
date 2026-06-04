import * as echarts from "echarts";

// Claude warm palette, registered once and referenced by name "claude".
echarts.registerTheme("claude", {
  color: ["#D97757", "#5B7B8A", "#7C8C6B", "#C99A6B", "#9A7AA0", "#A0564B"],
  backgroundColor: "transparent",
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
  tooltip: {
    backgroundColor: "#FFFFFF", borderColor: "#E8E3D9",
    textStyle: { color: "#1F1E1D", fontFamily: "Hanken Grotesk, Noto Sans TC, sans-serif" },
  },
});

export const CLAUDE_THEME = "claude";
