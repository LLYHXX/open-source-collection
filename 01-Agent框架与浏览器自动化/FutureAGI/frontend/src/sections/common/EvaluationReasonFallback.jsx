import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { EvaluationReasonFallbackMessage } from "src/utils/constant";

/**
 * Shared fallback display for evaluation/tool reason cells when there's an error
 * or no reason available. Used in EvalReasonCellRenderer, ToolReasonCellRenderer,
 * and CustomCellRender.
 */
const EvaluationReasonFallback = ({ message }) => (
  <Box
    sx={{
      display: "flex",
      flexDirection: "column",
      justifyContent: "center",
      alignItems: "center",
      flex: 1,
      height: "100%",
      minHeight: 0,
      px: 1.5,
      py: 0.5,
    }}
  >
    <Typography
      variant="body2"
      align="center"
      sx={{
        color: "text.secondary",
        opacity: 0.85,
        maxWidth: "100%",
        whiteSpace: "pre-wrap",
        wordBreak: "break-word",
      }}
    >
      {message || EvaluationReasonFallbackMessage}
    </Typography>
  </Box>
);

EvaluationReasonFallback.propTypes = {
  message: PropTypes.string,
};

export default EvaluationReasonFallback;
