import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const DatasetCompareAnnotationSummary = () => {
  return (
    <Box
      sx={{
        marginTop: "16px",
        borderRadius: "4px",
        backgroundColor: "blue.o5",
        border: "1px solid",
        borderColor: "blue.200",
        padding: "12px",
        display: "flex",
        flexDirection: "column",
        gap: 0.5,
      }}
    >
      <Typography
        typography={"s1"}
        fontWeight={"fontWeightSemiBold"}
        color="blue.500"
      >
        No Comparison Available
      </Typography>
      <Typography
        typography={"s3"}
        fontWeight={"fontWeightRegular"}
        color="blue.500"
      >
        Select an individual dataset to view its annotation summary
      </Typography>
    </Box>
  );
};

export default DatasetCompareAnnotationSummary;

DatasetCompareAnnotationSummary.propTypes = {
  selectedColumns: PropTypes.array,
  isCompare: PropTypes.bool,
  currentDataset: PropTypes.string,
  selectedDatasets: PropTypes.array,
  selectedIndex: PropTypes.number,
  commonColumn: PropTypes.array,
  baseColumn: PropTypes.string,
  selectedDatasetData: PropTypes.array,
};
