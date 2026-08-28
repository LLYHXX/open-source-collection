import React from "react";
import { useWorkflowRunStoreShallow } from "../store";
import ConfirmationDialog from "./ConfirmationDialog";

export default function ExecutionStopDialog() {
  const { dialog, close, confirm } = useWorkflowRunStoreShallow((s) => ({
    dialog: s.executionStopDialog,
    close: s.closeExecutionStopDialog,
    confirm: s.confirmExecutionStopDialog,
  }));

  return (
    <ConfirmationDialog
      open={dialog.open}
      onClose={close}
      onConfirm={confirm}
      title="Leave running workflow?"
      message="Your workflow will run in the background. You can find it in the Execution tab."
      confirmText="Leave"
      cancelText="Cancel"
      confirmColor="error"
    />
  );
}
