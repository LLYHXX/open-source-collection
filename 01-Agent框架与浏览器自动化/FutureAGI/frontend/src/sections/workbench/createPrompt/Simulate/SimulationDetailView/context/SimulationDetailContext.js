import { createContext, useContext } from "react";

export const SimulationDetailContext = createContext({
  simulationId: null,
  simulation: null,
  executions: [],
  executionsCount: 0,
  isLoading: false,
  isLoadingExecutions: false,
  refetchExecutions: () => {},
  refetchSimulation: () => {},
  selectedExecution: null,
  setSelectedExecution: (_a) => {},
  gridApi: null,
  setGridApi: () => {},
  getGridApi: () => null,
  refreshGrid: () => {},
  searchQuery: "",
  setSearchQuery: (_q) => {},
});

export const useSimulationDetailContext = () => {
  const context = useContext(SimulationDetailContext);
  if (!context) {
    throw new Error(
      "useSimulationDetailContext must be used within SimulationDetailProvider",
    );
  }
  return context;
};
