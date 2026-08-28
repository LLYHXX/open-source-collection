import React from "react";
import DeleteEvalConfirm from "./ConfirmDeleteEval";
import PropTypes from "prop-types";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import axios, { endpoints } from "src/utils/axios";
import { enqueueSnackbar } from "notistack";

const DeleteEval = ({
  open,
  setOpen,
  dataset,
  refreshGrid,
  userEval,
  hideDeleteColumn = false,
}) => {
  const queryClient = useQueryClient();

  const { mutate: deleteEval, isPending: deletingEval } = useMutation({
    // @ts-ignore
    mutationFn: ({ evalId, deleteColumn }) =>
      axios.delete(endpoints.develop.eval.deleteEval(dataset, evalId), {
        data: deleteColumn ? { delete_column: true } : undefined,
      }),
    onSuccess: () => {
      setOpen({ isDeleted: true });
      enqueueSnackbar("Evaluation deleted successfully", {
        variant: "success",
      });
      queryClient.invalidateQueries({
        queryKey: ["develop", "user-eval-list", dataset],
      });
      refreshGrid();
    },
    onError: () => {
      refreshGrid();
    },
  });

  const getEvalId = () => userEval?.evalId || userEval?.id;

  const handleDeleteEvalOnly = () => {
    // @ts-ignore
    deleteEval({ evalId: getEvalId() });
  };

  const handleDeleteEvalAndColumn = () => {
    // @ts-ignore
    deleteEval({ evalId: getEvalId(), deleteColumn: true });
  };

  return (
    <DeleteEvalConfirm
      open={open}
      onClose={() => setOpen({ isDeleted: false })}
      onConfirm={handleDeleteEvalOnly}
      onConfirmWithColumn={handleDeleteEvalAndColumn}
      isLoading={deletingEval}
      hideDeleteColumn={hideDeleteColumn}
    />
  );
};

export default DeleteEval;

DeleteEval.propTypes = {
  open: PropTypes.bool,
  setOpen: PropTypes.func,
  dataset: PropTypes.string,
  refreshGrid: PropTypes.func,
  userEval: PropTypes.object,
  hideDeleteColumn: PropTypes.bool,
};
