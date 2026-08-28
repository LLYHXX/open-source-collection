import PropTypes from "prop-types";
import React from "react";
import ConfirmationDialog from "./ConfirmationDialog";

export const DeleteAgentsDialog = ({
  open,
  onClose,
  onConfirm,
  agentCount,
  isLoading = false,
}) => {
  const message =
    agentCount === 1
      ? "Are you sure you want to delete 1 agent?"
      : `Are you sure you want to delete ${agentCount} agents?`;

  return (
    <ConfirmationDialog
      open={open}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Delete agents"
      message={message}
      confirmText="Delete"
      cancelText="Cancel"
      confirmColor="error"
      isLoading={isLoading}
    />
  );
};

DeleteAgentsDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
  agentCount: PropTypes.number.isRequired,
  isLoading: PropTypes.bool,
};

export default DeleteAgentsDialog;
