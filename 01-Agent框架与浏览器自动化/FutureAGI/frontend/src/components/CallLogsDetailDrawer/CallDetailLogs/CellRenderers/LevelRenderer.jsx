import { Box, Chip } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { typography } from "src/theme/typography";

const levelColor = {
  LOG: {
    color: "primary.main",
    backgroundColor: "action.hover",
  },
  INFO: {
    color: "blue.700",
    backgroundColor: "blue.o10",
  },
  WARN: {
    color: "orange.700",
    backgroundColor: "orange.o10",
  },
  ERROR: {
    color: "red.700",
    backgroundColor: "red.o10",
  },
};

const LevelRenderer = ({ value }) => {
  return (
    <Box>
      <Chip
        label={value}
        sx={{
          ...levelColor[value],
          paddingX: "12px",
          paddingY: "2px",
          borderRadius: "2px",

          "&:hover": {
            ...levelColor[value],
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

LevelRenderer.propTypes = {
  value: PropTypes.string,
};
export default LevelRenderer;
