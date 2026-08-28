import PropTypes from "prop-types";
import React from "react";
import ConfirmationDialog from "./ConfirmationDialog";

export const StopTemplateLoadingDialog = ({ open, onClose, onConfirm }) => {
  return (
    <ConfirmationDialog
      open={open}
      onClose={onClose}
      onConfirm={onConfirm}
      title="Are you sure you want to stop template loading?"
      message="Stopping now will erase your progress and restart the setup"
      confirmText="Stop"
      cancelText="Cancel"
      confirmColor="error"
    />
  );
};

StopTemplateLoadingDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
};

export default StopTemplateLoadingDialog;
