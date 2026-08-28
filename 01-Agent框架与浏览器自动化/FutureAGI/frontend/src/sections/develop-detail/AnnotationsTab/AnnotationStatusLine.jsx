import React from "react";
import { Box, Typography, LinearProgress } from "@mui/material";
import PropTypes from "prop-types";

const AnnotationsStatusLine = ({ value }) => {
  const progress = value?.progress || 0; // Ensure progress is provided in value
  const statusText = value?.text || "Unknown"; // Ensure status text is provided
  if (!value) return "";
  return (
    <Box display="flex" alignItems="center" justifyContent="center" gap={1.5}>
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{ width: "100px", height: "4px", borderRadius: "4px" }}
        color="success"
      />
      <Typography fontSize={12} color="text.secondary">
        {statusText}
      </Typography>
    </Box>
  );
};

AnnotationsStatusLine.propTypes = {
  value: PropTypes.object,
};

export default AnnotationsStatusLine;
