import React from "react";
import DeleteEvalConfirm from "./ConfirmDeleteEval";
import PropTypes from "prop-types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "react-router";
import axios, { endpoints } from "src/utils/axios";
import { enqueueSnackbar } from "notistack";
import { useEvaluationContext } from "./context/EvaluationContext";
import { useWorkbenchEvaluationContext } from "src/sections/workbench/createPrompt/Evaluation/context/WorkbenchEvaluationContext";

const DeleteEval = ({ open, setOpen, id, refreshGrid, userEval }) => {
  const queryClient = useQueryClient();
  const { module } = useEvaluationContext();
  const { experimentId } = useParams();
  const { showPrompts, showVariables, versions } =
    useWorkbenchEvaluationContext();
  const getEvalId = () => userEval?.evalId || userEval?.id;
  let endpoint = endpoints.develop.eval.deleteEval;
  if (module === "workbench") {
    endpoint = endpoints.develop.runPrompt.deleteEvalConfig;
  }

  const { mutate: deleteEval, isPending: deletingEval } = useMutation({
    /**
     *
     * @param {Object} data
     * @returns
     */
    mutationFn: ({ evalId, deleteColumn }) => {
      // Experiment evals are keyed by source_id=experiment_id on the backend.
      // Pass experiment_id in the body so the dataset-scoped lookup doesn't 404.
      const body = {};
      if (deleteColumn) body.delete_column = true;
      if (module === "experiment" && experimentId) {
        body.experiment_id = experimentId;
      }
      return axios.delete(endpoint(id, evalId), {
        data: Object.keys(body).length ? body : undefined,
      });
    },
    onSuccess: () => {
      setOpen({ isDeleted: true });
      enqueueSnackbar("Evaluation deleted successfully", {
        variant: "success",
      });
      if (module === "workbench") {
        queryClient.invalidateQueries({
          queryKey: ["workbench", "user-eval-list", id],
        });
        queryClient.invalidateQueries({
          queryKey: [
            "evaluations-workbench",
            showPrompts,
            showVariables,
            id,
            versions,
          ],
        });
      } else if (module === "experiment") {
        queryClient.invalidateQueries({
          queryKey: ["experiment", "user-eval-list"],
        });
        // Also the "develop" eval list — delete cascades across prefixes
        // because experiment evals are still bound to a dataset.
        queryClient.invalidateQueries({
          queryKey: ["develop", "user-eval-list"],
        });
        if (experimentId) {
          queryClient.invalidateQueries({
            queryKey: ["experiment", experimentId],
          });
          queryClient.invalidateQueries({ queryKey: ["experiment-list"] });
        }
        refreshGrid(null, true);
      } else {
        queryClient.invalidateQueries({
          queryKey: ["develop", "user-eval-list", id],
        });
      }
      refreshGrid();
    },
    onError: () => {
      refreshGrid(null, true);
    },
  });

  const handleDeleteEvalOnly = () => {
    deleteEval({ evalId: getEvalId() });
  };

  const handleDeleteEvalAndColumn = () => {
    deleteEval({ evalId: getEvalId(), deleteColumn: true });
  };

  return (
    <DeleteEvalConfirm
      open={open}
      onClose={() => setOpen({ isDeleted: false })}
      onConfirm={handleDeleteEvalOnly}
      onConfirmWithColumn={handleDeleteEvalAndColumn}
      isLoading={deletingEval}
    />
  );
};

export default DeleteEval;

DeleteEval.propTypes = {
  open: PropTypes.bool,
  setOpen: PropTypes.func,
  id: PropTypes.string,
  refreshGrid: PropTypes.func,
  userEval: PropTypes.object,
};
