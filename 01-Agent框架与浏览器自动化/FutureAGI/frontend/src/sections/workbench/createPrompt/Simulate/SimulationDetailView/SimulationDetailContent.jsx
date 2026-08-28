import { Box } from "@mui/material";
import React from "react";
import SimulationExecutionsGrid from "./SimulationExecutionsGrid";

const SimulationDetailContent = () => {
  return (
    <Box
      display="flex"
      flexDirection="column"
      width="100%"
      height="100%"
      sx={{
        overflow: "hidden",
        flex: 1,
      }}
    >
      <SimulationExecutionsGrid />
    </Box>
  );
};

export default SimulationDetailContent;
