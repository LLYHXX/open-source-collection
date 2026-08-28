import React, { useCallback } from "react";
import PropTypes from "prop-types";
import { BaseSelectionActions } from "src/sections/common/simulation";
import { useSimulationEvaluationStoreShallow } from "./states";
import { DRAWER_OPEN_ENUMS } from "./common";

const SimulationExecutionsSelection = ({ selectedCount, clearSelection }) => {
  const { setOpenEvaluation } = useSimulationEvaluationStoreShallow((s) => ({
    setOpenEvaluation: s.setOpenEvaluation,
  }));

  const handleRunEvals = useCallback(() => {
    setOpenEvaluation(DRAWER_OPEN_ENUMS.EVALS);
  }, [setOpenEvaluation]);

  const handleDelete = useCallback(() => {
    setOpenEvaluation(DRAWER_OPEN_ENUMS.DELETE);
  }, [setOpenEvaluation]);

  return (
    <BaseSelectionActions
      selectedCount={selectedCount}
      onRunEvals={handleRunEvals}
      onDelete={handleDelete}
      onClearSelection={clearSelection}
    />
  );
};

SimulationExecutionsSelection.propTypes = {
  selectedCount: PropTypes.number.isRequired,
  clearSelection: PropTypes.func.isRequired,
};

export default SimulationExecutionsSelection;
