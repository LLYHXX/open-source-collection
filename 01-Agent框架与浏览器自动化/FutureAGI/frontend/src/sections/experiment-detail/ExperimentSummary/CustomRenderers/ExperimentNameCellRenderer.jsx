import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import CompareDatasetSummaryIcon from "src/sections/develop-detail/DatasetSummaryTab/CompareDatasetSummaryIcon";

const ExperimentNameCellRenderer = (props) => {
  const {
    value,
    node: { rowIndex },
  } = props;

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1,

        width: "100%",
        height: "100%",
      }}
    >
      <CompareDatasetSummaryIcon index={rowIndex} />
      <Box sx={{ whiteSpace: "normal", wordBreak: "break-word" }}>{value}</Box>
    </Box>
  );
};

ExperimentNameCellRenderer.propTypes = {
  value: PropTypes.string,
  data: PropTypes.object,
  node: PropTypes.object,
};

export default ExperimentNameCellRenderer;
