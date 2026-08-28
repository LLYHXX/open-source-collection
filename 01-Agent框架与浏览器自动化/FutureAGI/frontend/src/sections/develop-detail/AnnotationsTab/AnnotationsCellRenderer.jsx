import { Box, Chip } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const statusColor = {
  NotStarted: "default",
  Running: "primary",
  Completed: "success",
  Editing: "warning",
  Inactive: "default",
  Failed: "error",
};

const AnnotationsCellRenderer = ({ value }) => {
  return (
    <Box>
      <Chip
        variant="soft"
        label={value}
        size="small"
        color={statusColor[value]}
      />
    </Box>
  );
};

AnnotationsCellRenderer.propTypes = {
  value: PropTypes.string,
};

export default AnnotationsCellRenderer;
