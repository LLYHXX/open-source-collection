import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

import RunDetailsCard from "../CompareDrawer2/RunDetailsCard";

const getDataType = (value) => {
  if (Array.isArray(value)) {
    return "array";
  }
  if (typeof value === "object" && value !== null) {
    return "json";
  }
  return typeof value;
};

const TraceDataList = ({ traceData }) => {
  const inputType = getDataType(traceData?.input);
  const outputType = getDataType(traceData?.output);

  const inputValue =
    inputType === "json" || inputType === "array"
      ? JSON.stringify(traceData?.input, null, 2)
      : traceData?.input;

  const outputValue =
    outputType === "json" || outputType === "array"
      ? JSON.stringify(traceData?.output, null, 2)
      : traceData?.output;

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 2, width: "100%" }}
    >
      <RunDetailsCard
        column={{ headerName: "Input", dataType: inputType }}
        value={{ cellValue: inputValue }}
        allowCopy
      />
      <RunDetailsCard
        column={{ headerName: "Output", dataType: outputType }}
        value={{ cellValue: outputValue }}
        allowCopy
      />
    </Box>
  );
};

TraceDataList.propTypes = {
  traceData: PropTypes.object,
};

export default TraceDataList;
