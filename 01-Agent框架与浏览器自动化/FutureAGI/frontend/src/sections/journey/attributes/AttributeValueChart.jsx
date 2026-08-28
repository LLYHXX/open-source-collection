import PropTypes from "prop-types";
import ReactApexChart from "react-apexcharts";
import { useTheme } from "@mui/material/styles";
import { Box } from "@mui/material";

const AttributeValueChart = ({ data, type: _type }) => {
  const theme = useTheme();

  if (!data || data.length === 0) return null;

  const chartOptions = {
    chart: {
      type: "bar",
      toolbar: { show: false },
      background: "transparent",
    },
    plotOptions: {
      bar: {
        horizontal: true,
        borderRadius: 4,
        barHeight: "60%",
      },
    },
    dataLabels: {
      enabled: true,
      formatter: (val) => `${val.toFixed(1)}%`,
      style: { fontSize: "11px" },
    },
    xaxis: {
      categories: data.map((d) => String(d.value)),
      labels: { formatter: (val) => `${val}%` },
      max: 100,
    },
    yaxis: {
      labels: {
        maxWidth: 160,
        style: { fontSize: "12px" },
      },
    },
    colors: [theme.palette.primary.main],
    tooltip: {
      y: {
        formatter: (val, { dataPointIndex }) =>
          `${data[dataPointIndex]?.count?.toLocaleString()} spans (${val.toFixed(1)}%)`,
      },
    },
    grid: {
      borderColor: theme.palette.divider,
      xaxis: { lines: { show: true } },
      yaxis: { lines: { show: false } },
    },
    theme: { mode: theme.palette.mode },
  };

  const series = [
    { name: "Distribution", data: data.map((d) => d.percentage || 0) },
  ];

  const chartHeight = Math.max(data.length * 36, 120);

  return (
    <Box sx={{ width: "100%" }}>
      <ReactApexChart
        options={chartOptions}
        series={series}
        type="bar"
        height={chartHeight}
      />
    </Box>
  );
};

AttributeValueChart.propTypes = {
  data: PropTypes.arrayOf(
    PropTypes.shape({
      value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      count: PropTypes.number,
      percentage: PropTypes.number,
    }),
  ),
  type: PropTypes.string,
};

export default AttributeValueChart;
