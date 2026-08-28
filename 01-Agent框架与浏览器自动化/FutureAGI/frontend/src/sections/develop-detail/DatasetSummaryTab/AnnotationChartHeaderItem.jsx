import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const AnnotationChartHeaderItem = ({ title, value }) => {
  return (
    <Box
      display="flex"
      flexDirection={"column"}
      gap={"2px"}
      padding={1.5}
      sx={{
        backgroundColor: "background.neutral",
        border: "1px solid",
        borderColor: "divider",
        borderRadius: "4px",
      }}
    >
      <Typography
        typography={"s2_1"}
        fontWeight={"fontWeightMedium"}
        color="text.primary"
      >
        {title}
      </Typography>

      <Typography
        typography={"m1"}
        fontWeight={"fontWeightSemiBold"}
        color="text.primary"
      >
        {value || value === 0
          ? isNaN(value)
            ? value
            : Number.isInteger(Number(value))
              ? value
              : Number(value).toFixed(2)
          : "N/A"}
      </Typography>
    </Box>
  );
};

export default AnnotationChartHeaderItem;

AnnotationChartHeaderItem.propTypes = {
  title: PropTypes.string,
  value: PropTypes.string,
};
