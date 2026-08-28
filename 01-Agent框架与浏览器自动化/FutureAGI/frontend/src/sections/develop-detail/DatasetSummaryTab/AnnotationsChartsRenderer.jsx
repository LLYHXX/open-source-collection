import React from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";
import { ShowComponent } from "src/components/show";
import AnnotationChartHeader from "./AnnotationChartHeader";
import DonutChart from "./ChartsContainer/DonutChart";
import TextChart from "./ChartsContainer/TextChart";
import AnnotationBarChartWrapper from "./ChartsContainer/AnnotationBarChartWrapper";
// import ColumnBarChart from "./ChartsContainer/ColumnBarChart";

const AnnotationsChartsRenderer = ({ labels = [], names = [] }) => {
  return (
    <Box display={"flex"} gap={2} flexWrap={"wrap"} width="100%">
      {labels.map((item, index) => {
        const { labelName, type } = item;
        const donutChart = {};
        if (type == "categorical") {
          const value = Object.values(item.graphData || {});
          donutChart["label"] = Object.keys(item.graphData || {});
          donutChart["data"] = [
            { name: labelName, value: value.map((temp) => temp * 100) },
          ];
        }

        return (
          <Box
            key={index}
            sx={{
              width: "calc(50% - 8px)",
              border: "1px solid",
              borderColor: "divider",
              borderRadius: 1,
              padding: 2,
              display: "flex",
              flexDirection: "column",
              gap: 2,
            }}
          >
            <AnnotationChartHeader chartHeading={labelName} item={item || {}} />
            <ShowComponent condition={type === "categorical"}>
              <DonutChart
                height={350}
                type="annotation"
                data={donutChart.data || []}
                graphLabels={donutChart.label || []}
                plotOptions={{
                  pie: {
                    donut: {
                      labels: {
                        show: true,
                        total: {
                          showAlways: true,
                          show: true,
                          label: "Total",
                          formatter: function () {
                            return item.countRecords || 0;
                          },
                        },
                        value: {
                          show: true,
                          formatter: function (val) {
                            return val.toFixed(1);
                          },
                        },
                      },
                    },
                  },
                }}
                options={{
                  tooltip: {
                    enabled: true,
                    followCursor: true,
                    custom: function ({ series, seriesIndex, w }) {
                      const label = w.globals.labels[seriesIndex];
                      const value = series[seriesIndex];
                      return `<div style="padding: 8px 12px; background: var(--bg-neutral); color: var(--text-primary); border: 1px solid var(--border-default); border-radius: 4px; font-size: 14px;">
                        <strong>${label}</strong><br/>
                        ${value.toFixed(1)}%
                      </div>`;
                    },
                  },
                }}
              />
            </ShowComponent>
            <ShowComponent condition={type === "text"}>
              <TextChart
                height={350}
                data={item?.keyTerms?.map((temp) => ({ name: temp })) || []}
                graphLabels={["Key terms and patterns"]}
              />
            </ShowComponent>
            <ShowComponent condition={item.type === "numeric"}>
              <AnnotationBarChartWrapper item={item} names={names} />
            </ShowComponent>
            {/* <ShowComponent condition={item.type === "thumb"}>
              <ColumnBarChart
                height={350}
                data={[
                  { name: "Thumb", value: graphData.map((item) => item.value) },
                ]}
                graphLabels={graphData.map((item) => item.name) || []}
                colors={["green", "red"]}
                plotOptions={{
                  bar: {
                    borderRadius: 4,
                    horizontal: false,
                    columnWidth: "40%",
                    distributed: true,
                    borderRadiusApplication: "end",
                  },
                }}
              />
            </ShowComponent> */}
            {/* <ShowComponent condition={item.type === "star"}>
              <ColumnBarChart
                height={350}
                data={[
                  { name: "star", value: graphData?.map((item) => item.value) },
                ]}
                graphLabels={graphData?.map((item) => item.name) || []}
                colors={["red", "orange", "yellow", "blue", "green"]}
                plotOptions={{
                  bar: {
                    borderRadius: 4,
                    horizontal: false,
                    columnWidth: "40%",
                    distributed: true,
                    borderRadiusApplication: "end",
                  },
                }}
              />
            </ShowComponent> */}
          </Box>
        );
      })}
    </Box>
  );
};

export default AnnotationsChartsRenderer;

AnnotationsChartsRenderer.propTypes = {
  labels: PropTypes.array,
  names: PropTypes.array,
};
