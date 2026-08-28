import { Box, Typography } from "@mui/material";
import React from "react";

const NoOptimizationSelected = () => {
  return (
    <Box
      sx={{
        minHeight: "714px",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        position: "relative",
      }}
    >
      <Box
        sx={{ display: "flex", flexDirection: "column", alignItems: "center" }}
      >
        <Box
          component="img"
          alt="empty content"
          src={"/assets/icons/components/ic_extra_scroll.svg"}
          sx={{ width: 1, maxWidth: 160 }}
        />
        <Typography
          variant="subtitle1"
          sx={{ width: "250px", textAlign: "center" }}
          id="no-models-text"
        >
          Please select an optimization
        </Typography>
      </Box>
    </Box>
  );
};

export default NoOptimizationSelected;
