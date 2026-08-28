import { Box, Typography } from "@mui/material";
import React from "react";
import SVGColor from "src/components/svg-color";
import "./prompt-loading.css";

const PromptLoading = () => {
  return (
    <Box
      component="span"
      sx={{ display: "inline-flex", alignItems: "center", gap: 1 }}
      className="prompt-loading-container"
    >
      <SVGColor
        src="/assets/icons/components/ic_falling_start.svg"
        sx={{ width: "20px", height: "20px", flexShrink: 0 }}
        className="prompt-loading-icon"
      />
      <Typography
        typography="s1"
        sx={{ display: "flex", alignItems: "center", gap: 1 }}
        className="prompt-loading"
      >
        Creating your final output...
      </Typography>
    </Box>
  );
};

export default PromptLoading;
