import { Box, Chip } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { typography } from "src/theme/typography";
import _ from "lodash";

const categoryColor = {
  system: {
    color: "green.700",
    backgroundColor: "green.o10",
  },
  voice: {
    color: "pink.700",
    backgroundColor: "pink.o10",
  },
  transcriber: {
    color: "blue.700",
    backgroundColor: "blue.o10",
  },
  endpointing: {
    color: "orange.700",
    backgroundColor: "orange.o10",
  },
  model: {
    color: "primary.main",
    backgroundColor: "action.hover",
  },
  latency: {
    color: "red.700",
    backgroundColor: "red.o10",
  },
  transport: {
    color: "orange.500",
    backgroundColor: "orange.o5",
  },
  webhook: {
    color: "green.400",
    backgroundColor: "green.o5",
  },
};

const CategoryRenderer = ({ value }) => {
  return (
    <Box>
      <Chip
        label={_.capitalize(value)}
        sx={{
          ...categoryColor[value],
          paddingX: "12px",
          paddingY: "2px",
          borderRadius: "2px",

          "&:hover": {
            ...categoryColor[value],
          },
          "& .MuiChip-label": {
            padding: 0,
            ...typography.s3,
            fontWeight: "fontWeightMedium",
          },
        }}
      />
    </Box>
  );
};

export default CategoryRenderer;

CategoryRenderer.propTypes = {
  value: PropTypes.string,
};
