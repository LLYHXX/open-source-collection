import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React, { useEffect } from "react";
import SimulationDetailHeader from "./SimulationDetailHeader";
import SimulationDetailContent from "./SimulationDetailContent";
import { SimulationDetailProvider } from "./context/SimulationDetailProvider";
import { resetState } from "src/sections/test/TestRuns/states";

const SimulationDetailView = ({ simulationId, onBack }) => {
  useEffect(() => {
    return () => resetState();
  }, []);

  return (
    <SimulationDetailProvider simulationId={simulationId}>
      <Box
        display="flex"
        flexDirection="column"
        width="100%"
        height="100%"
        gap={1}
        sx={{
          overflow: "hidden",
        }}
      >
        <SimulationDetailHeader onBack={onBack} />
        <SimulationDetailContent />
      </Box>
    </SimulationDetailProvider>
  );
};

SimulationDetailView.propTypes = {
  simulationId: PropTypes.string.isRequired,
  onBack: PropTypes.func.isRequired,
};

export default SimulationDetailView;
