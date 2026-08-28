import { Box } from "@mui/material";
import React from "react";
import OptimizeAgentHeaderComponent from "../OptimizeAgentDrawer.jsx/OptimizeAgentHeaderComponent";

const OptimizeFlow = () => {
  return (
    <Box
      sx={{
        width: "80vw",
        padding: 2,
        height: "100%",
        display: "flex",
        flexDirection: "column",
        gap: 2,
      }}
    >
      <OptimizeAgentHeaderComponent
        isDrawer={true}
        onClose={() => {}}
        optimization={{
          id: "OPT-00001",
          name: "Optimization-run-1",
          theorem: "Random Search",
          status: "queued",
          runTime: null,
          completedAt: null,
        }}
        simulationId="SIM-00001"
        executionId="EXEC-00001"
      />
    </Box>
  );
};

export default OptimizeFlow;
