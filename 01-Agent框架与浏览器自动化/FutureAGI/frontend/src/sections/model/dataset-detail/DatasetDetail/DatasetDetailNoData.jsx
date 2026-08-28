import { Box, Typography } from "@mui/material";
import React from "react";

export const DatasetDetailNoData = () => {
  return (
    <Box
      sx={{
        minHeight: "calc(100vh - 230px)",
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
          id="no-dataset-text"
        >
          No data points to show
        </Typography>
      </Box>
    </Box>
  );
};
