import { useCallback } from "react";
import { useAgentPlaygroundStoreShallow } from "../store";

/**
 * Hook to handle draft confirmation before executing an action.
 * If the current agent is a draft, shows a confirmation dialog.
 * If not a draft, executes the callback directly.
 *
 * @returns {Object} - { confirmIfDraft: Function, isDraft: boolean }
 */
export function useDraftConfirmation() {
  const { currentAgent, openDraftConfirmDialog } =
    useAgentPlaygroundStoreShallow((s) => ({
      currentAgent: s.currentAgent,
      openDraftConfirmDialog: s.openDraftConfirmDialog,
    }));

  // Check if current agent is a draft
  // An agent is considered a draft if it has isDraft flag set to true
  // or if it doesn't have a versionId (unsaved new agent)
  const isDraft = currentAgent?.is_draft === true || !currentAgent?.version_id;

  /**
   * Execute a callback, with confirmation if the agent is a draft.
   * @param {Function} callback - The function to execute
   * @param {string} [customMessage] - Optional custom message for the dialog
   */
  const confirmIfDraft = useCallback(
    (callback, customMessage = null) => {
      if (isDraft) {
        openDraftConfirmDialog(callback, customMessage);
      } else {
        callback();
      }
    },
    [isDraft, openDraftConfirmDialog],
  );

  return {
    confirmIfDraft,
    isDraft,
  };
}

export default useDraftConfirmation;
