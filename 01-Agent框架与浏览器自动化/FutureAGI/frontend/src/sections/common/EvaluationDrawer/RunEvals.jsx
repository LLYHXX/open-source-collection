import React from "react";
import PropTypes from "prop-types";
import { useRunEvalMutation } from "./getEvalsList";
import ConfirmRunEvaluations from "./ConfirmRunEvaluations";
import { useEvaluationContext } from "./context/EvaluationContext";
import { useWorkbenchEvaluationContext } from "src/sections/workbench/createPrompt/Evaluation/context/WorkbenchEvaluationContext";

const RunEvals = ({ open, userEvals, id, refreshGrid, onClose }) => {
  const { module } = useEvaluationContext();
  const { versions } = useWorkbenchEvaluationContext();
  const commonOnSuccess = () => {
    onClose();
    refreshGrid?.(null, true);
  };

  const { mutate: runEval } = useRunEvalMutation(id, commonOnSuccess, module);

  const handleConfirm = (evalsToRun) => {
    const ids = evalsToRun.map((e) => e.id);
    let payload = {};
    switch (module) {
      case "workbench":
        payload = {
          version_to_run: versions,
          prompt_eval_config_ids: ids,
        };
        break;
      case "experiment":
        payload = {
          eval_template_ids: ids,
        };
        break;
      default:
        payload = {
          user_eval_ids: ids,
        };
        break;
    }

    runEval(payload);
    onClose?.();
  };

  return (
    <ConfirmRunEvaluations
      open={open}
      onClose={onClose}
      selectedUserEvalList={userEvals}
      onConfirm={handleConfirm}
    />
  );
};

RunEvals.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  userEvals: PropTypes.array,
  id: PropTypes.string,
  refreshGrid: PropTypes.func,
};

export default RunEvals;
