import {
  createGridSelectionStore,
  createEvaluationDialogStore,
} from "src/sections/common/simulation";

// Store for simulation executions grid selection
const simulationExecutionsGridStore = createGridSelectionStore({
  trackTotalRowCount: true,
});
export const useSimulationExecutionsGridStore =
  simulationExecutionsGridStore.store;
export const useSimulationExecutionsGridStoreShallow =
  simulationExecutionsGridStore.useStoreShallow;

// Store for simulation evaluation dialog
const simulationEvaluationStore = createEvaluationDialogStore("openEvaluation");
export const useSimulationEvaluationStore = simulationEvaluationStore.store;
export const useSimulationEvaluationStoreShallow =
  simulationEvaluationStore.useStoreShallow;

export const resetSimulationDetailState = () => {
  useSimulationExecutionsGridStore.getState().reset();
  useSimulationEvaluationStore.setState({ openEvaluation: null });
};
