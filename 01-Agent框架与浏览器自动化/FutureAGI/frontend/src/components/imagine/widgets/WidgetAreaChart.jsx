import React from "react";
import PropTypes from "prop-types";
import ReactApexChart from "react-apexcharts";
import { useTheme } from "@mui/material/styles";

const COLORS = [
  "#7B56DB",
  "#1ABCFE",
  "#FF6B6B",
  "#2ECB71",
  "#F7B731",
  "#E84393",
  "#0984E3",
  "#FD7E14",
  "#00CEC9",
  "#A29BFE",
];

export default function WidgetAreaChart({ config }) {
  const theme = useTheme();
  const isDark = theme.palette.mode === "dark";

  const series = config.series || [];
  const categories = config.categories || [];
  const stacked = config.stacked ?? false;

  const options = {
    chart: {
      type: "area",
      stacked,
      background: "transparent",
      foreColor: isDark ? "#a1a1aa" : "#666",
      toolbar: { show: false },
    },
    theme: { mode: isDark ? "dark" : "light" },
    colors: config.colors || COLORS,
    stroke: { width: 2, curve: "smooth" },
    fill: { type: "gradient", gradient: { opacityFrom: 0.4, opacityTo: 0.05 } },
    dataLabels: { enabled: false },
    xaxis: { categories },
    grid: {
      borderColor: isDark ? "#27272a" : "#f0f0f0",
      strokeDashArray: 3,
    },
    tooltip: { theme: isDark ? "dark" : "light" },
    legend: {
      show: series.length > 1,
      position: "top",
      horizontalAlign: "left",
      fontSize: "12px",
    },
  };

  return (
    <ReactApexChart
      options={options}
      series={series}
      type="area"
      height="100%"
    />
  );
}

WidgetAreaChart.propTypes = { config: PropTypes.object.isRequired };
