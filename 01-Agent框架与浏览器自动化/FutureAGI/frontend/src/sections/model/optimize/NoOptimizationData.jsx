import { Box, Typography, useTheme } from "@mui/material";
import React, { useEffect } from "react";
import Xarrow, { useXarrow } from "react-xarrows";

const NoOptimizationData = () => {
  const updateXarrow = useXarrow();

  const theme = useTheme();

  useEffect(() => {
    updateXarrow();
  });

  return (
    <Box
      sx={{
        height: "calc(100vh - 250px)",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        flexDirection: "column",
      }}
    >
      <Box
        component="img"
        alt="empty content"
        src={"/assets/icons/components/ic_extra_scroll.svg"}
        sx={{ width: 1, maxWidth: 230 }}
      />
      <Typography
        variant="subtitle1"
        sx={{ width: "250px", textAlign: "center" }}
        id="no-optimization-text"
      >
        To optimize a dataset, click on “Optimize dataset”
      </Typography>
      <Xarrow
        start="no-optimization-text"
        end="add-optimization-button"
        dashness
        strokeWidth={2}
        color={theme.palette.primary.main}
        startAnchor={{ position: "right", offset: { x: -50, y: 12 } }}
        endAnchor={{ position: "bottom", offset: { x: 0, y: 10 } }}
        tailShape="circle"
        showTail
        headShape="arrow1"
      />
    </Box>
  );
};

export default NoOptimizationData;
