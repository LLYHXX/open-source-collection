import { Box, Typography } from "@mui/material";
import React from "react";
import { useSearchParams } from "react-router-dom";

const SimulateActions = () => {
  const [searchParams] = useSearchParams();
  const selectedSimulationId = searchParams.get("simulation");

  // Don't show the header when viewing a simulation detail
  if (selectedSimulationId) {
    return null;
  }

  return (
    <Box
      display="flex"
      justifyContent="space-between"
      alignItems="center"
      width="100%"
      py={1}
    >
      <Typography variant="subtitle1" fontWeight={600}>
        Simulation Runs
      </Typography>
    </Box>
  );
};

export default SimulateActions;
