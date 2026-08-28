import { Box } from "@mui/material";
import React, { useRef, useState } from "react";
import { useParams } from "react-router";
import { useSearchParams } from "react-router-dom";
import CreateSimulationModal from "../CreateSimulationModal";
import SimulationDetailView from "../SimulationDetailView";
import RunTestsContent from "src/components/run-tests/RunTestsContent";
import { SIMULATION_TYPE } from "src/components/run-tests/common";

const SimulateContent = () => {
  const { id: promptTemplateId } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedSimulationId = searchParams.get("simulation");
  const gridRef = useRef(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const handleBackToList = () => {
    const newParams = new URLSearchParams(searchParams);
    newParams.delete("simulation");
    setSearchParams(newParams);
  };

  const handleRowClick = (row) => {
    if (!row?.id) return;
    const newParams = new URLSearchParams(searchParams);
    newParams.set("simulation", row.id);
    setSearchParams(newParams);
  };

  const handleCreateSuccess = (simulationId) => {
    setIsCreateModalOpen(false);
    if (simulationId) {
      const newParams = new URLSearchParams(searchParams);
      newParams.set("simulation", simulationId);
      setSearchParams(newParams);
    } else {
      gridRef.current?.api?.refreshServerSide({ purge: true });
    }
  };

  // If a simulation is selected, show the detail view
  if (selectedSimulationId) {
    return (
      <SimulationDetailView
        simulationId={selectedSimulationId}
        onBack={handleBackToList}
      />
    );
  }

  return (
    <Box
      display="flex"
      flexDirection="column"
      width="100%"
      height="100%"
      sx={{
        overflow: "auto",
      }}
    >
      <RunTestsContent
        simulationType={SIMULATION_TYPE.PROMPT}
        promptTemplateId={promptTemplateId}
        showHeader={false}
        showSearch={true}
        onRowClick={handleRowClick}
        onCreateClick={() => setIsCreateModalOpen(true)}
        createButtonText="Create Simulation"
        emptyTitle="No simulations yet"
        emptyDescription="Create a simulation to test your prompt with different scenarios."
        emptyIcon="/assets/icons/navbar/ic_get_started.svg"
        gridRef={gridRef}
      />

      <CreateSimulationModal
        open={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={handleCreateSuccess}
      />
    </Box>
  );
};

export default SimulateContent;
