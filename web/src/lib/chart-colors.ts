import { useEffect, useState } from "react";

export interface ChartColors {
  accent: string; secondary: string; muted: string; grid: string; ink: string;
  series: string[]; heat: string[];
}

const DARK: ChartColors = {
  accent: "#3DBB7A", secondary: "#F2B84B", muted: "#84908A", grid: "#2A3538", ink: "#ECEFEC",
  series: ["#3DBB7A", "#F2B84B", "#7FA9B6", "#9BB089", "#B597BA", "#C2766A"],
  heat: ["#12201A", "#256B48", "#3DBB7A", "#7FE0AE"],
};
const LIGHT: ChartColors = {
  accent: "#1E8A56", secondary: "#B8791C", muted: "#5A6560", grid: "#D2D8D3", ink: "#12181A",
  series: ["#1E8A56", "#B8791C", "#3F6B78", "#5C7355", "#8A6D9C", "#A0564B"],
  heat: ["#EAF3EC", "#8FCDA9", "#3DBB7A", "#1E8A56"],
};

/** Terrain palette for canvas charts (which cannot read CSS vars). */
export function chartColors(dark: boolean): ChartColors { return dark ? DARK : LIGHT; }

/** Tracks the site theme by listening for the themechange event the toggle fires. */
export function useDark(): boolean {
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

export function useChartColors(): ChartColors { return chartColors(useDark()); }
