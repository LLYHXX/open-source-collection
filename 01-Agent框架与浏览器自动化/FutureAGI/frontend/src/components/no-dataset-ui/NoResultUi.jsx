import { Box, Typography } from "@mui/material";
import React from "react";

export default function NoResultUi() {
  return (
    <Box>
      <Typography
        typography={"s1"}
        fontWeight={"fontWeightMedium"}
        color={"text.primary"}
      >
        No Results Found
      </Typography>
    </Box>
  );
}
