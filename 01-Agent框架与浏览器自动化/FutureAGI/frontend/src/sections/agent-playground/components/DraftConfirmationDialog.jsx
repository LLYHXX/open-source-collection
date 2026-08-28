import React from "react";
import { useAgentPlaygroundStoreShallow } from "../store";
import { useDeleteVersion } from "src/api/agent-playground/agent-playground";
import ConfirmationDialog from "./ConfirmationDialog";

const DEFAULT_MESSAGE =
  "Current progress will be discarded. Save your changes before proceeding.";

/**
 * Global draft confirmation dialog for the Agent Playground.
 * Shows a warning when the user attempts to perform an action that would
 * discard their unsaved draft changes.
 * If the current agent is a draft, clicking "Discard Changes" will delete
 * the draft version via API before executing the stored callback.
 */
export const DraftConfirmationDialog = () => {
  const {
    draftConfirmDialog,
    closeDraftConfirmDialog,
    confirmDraftDialog,
    currentAgent,
  } = useAgentPlaygroundStoreShallow((s) => ({
    draftConfirmDialog: s.draftConfirmDialog,
    closeDraftConfirmDialog: s.closeDraftConfirmDialog,
    confirmDraftDialog: s.confirmDraftDialog,
    currentAgent: s.currentAgent,
  }));

  const { mutate: deleteVersion, isPending } = useDeleteVersion();

  const handleConfirm = () => {
    if (currentAgent?.is_draft && currentAgent?.version_id) {
      deleteVersion(
        { graphId: currentAgent.id, versionId: currentAgent.version_id },
        { onSuccess: () => confirmDraftDialog() },
      );
    } else {
      confirmDraftDialog();
    }
  };

  return (
    <ConfirmationDialog
      open={draftConfirmDialog.open}
      onClose={closeDraftConfirmDialog}
      onConfirm={handleConfirm}
      title="Unsaved Changes"
      message={draftConfirmDialog.message || DEFAULT_MESSAGE}
      confirmText="Discard Changes"
      cancelText="Cancel"
      confirmColor="error"
      isLoading={isPending}
    />
  );
};

export default DraftConfirmationDialog;
