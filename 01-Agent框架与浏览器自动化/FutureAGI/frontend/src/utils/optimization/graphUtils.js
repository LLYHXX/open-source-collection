/**
 * Shared graph utilities for optimization results.
 *
 * Used by both:
 * - DatasetOptimizationResultGraph
 * - OptimizationResultGraph (simulation)
 */

import { getUniqueColorPalette } from "../utils";

/**
 * Generate category labels for optimization trial graph.
 *
 * @param {number} length - Number of data points (including baseline)
 * @returns {string[]} Array of category labels ["Baseline", "Trial 1", "Trial 2", ...]
 */
export const getCategories = (length) => {
  if (length === 0) return [];
  const categories = ["Baseline"];
  for (let i = 1; i < length; i++) {
    categories.push(`Trial ${i}`);
  }
  return categories;
};

/**
 * Generate HTML content for graph tooltip.
 *
 * @param {string} trialName - Name of the trial (e.g., "Baseline", "Trial 1")
 * @param {string} seriesName - Name of the eval metric series
 * @param {number} value - Score value (as percentage 0-100)
 * @param {string} color - Color for the series indicator dot
 * @returns {string} HTML string for tooltip content
 */
export const getGraphTooltipComponent = (
  trialName,
  seriesName,
  value,
  color,
) => {
  return `
    <div style="
      background: var(--bg-paper);
      padding: 12px;
      box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.1);
      font-family: 'IBM Plex Sans', sans-serif;
      min-width: 160px;
    ">
      <div style="
        font-size: 12px;
        font-weight: 500;
        color: var(--text-primary);
        margin-bottom: 8px;
      ">
        ${trialName}
      </div>
      <div style="
        display: flex;
        align-items: center;
        gap: 8px;
      ">
        <div style="
          width: 12px;
          height: 12px;
          border-radius: 50%;
          background-color: ${color};
          flex-shrink: 0;
        "></div>
        <div style="font-size: 12px; color: var(--text-muted);">
          <span style="font-weight: 500;">${seriesName}:</span>
          <span style="font-weight: 600; color: var(--text-primary); margin-left: 4px;">
            ${typeof value === "number" ? Math.round(value) : value}%
          </span>
        </div>
      </div>
    </div>
  `;
};

/**
 * Update crosshair color to match the hovered series.
 *
 * @param {Object} chartContext - ApexCharts context object
 * @param {number|undefined} seriesIndex - Index of the hovered series, or undefined to reset
 */
export const updateCrosshairColor = (chartContext, seriesIndex) => {
  if (!chartContext?.w?.globals?.dom?.baseEl) return;

  const color =
    seriesIndex !== undefined
      ? getUniqueColorPalette(seriesIndex)?.tagForeground ||
        getUniqueColorPalette(0).tagForeground
      : getUniqueColorPalette(0).tagForeground;

  const baseEl = chartContext.w.globals.dom.baseEl;

  // Try multiple ways to find the crosshair
  let crosshairLine = baseEl.querySelector(".apexcharts-xcrosshairs line");

  // If not found, try finding the group first
  if (!crosshairLine) {
    const crosshairGroup = baseEl.querySelector(".apexcharts-xcrosshairs");
    crosshairLine = crosshairGroup?.querySelector("line");
  }

  // If still not found, try direct line with class
  if (!crosshairLine) {
    crosshairLine = baseEl.querySelector("line.apexcharts-xcrosshairs");
  }

  if (crosshairLine) {
    crosshairLine.setAttribute("stroke", color);
    crosshairLine.setAttribute("stroke-dasharray", "4");
    crosshairLine.style.stroke = color;
    crosshairLine.style.strokeDasharray = "4";
  }
};

/**
 * Default chart options for optimization graphs.
 * Can be extended/overridden as needed.
 */
export const getBaseChartOptions = () => ({
  chart: {
    type: "line",
    toolbar: {
      show: false,
    },
    zoom: {
      enabled: false,
    },
  },
  stroke: {
    curve: "smooth",
    width: 2,
  },
  markers: {
    size: 4,
    hover: {
      size: 6,
    },
  },
  grid: {
    borderColor: "var(--border-default)",
    strokeDashArray: 4,
  },
  legend: {
    show: true,
    position: "top",
    horizontalAlign: "left",
  },
  yaxis: {
    min: 0,
    max: 1,
    decimalsInFloat: 2,
    labels: {
      formatter: (value) => value?.toFixed(2) ?? "-",
    },
  },
});
