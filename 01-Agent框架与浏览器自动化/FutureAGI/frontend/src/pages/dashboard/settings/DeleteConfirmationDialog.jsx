import React from "react";
import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Button,
} from "@mui/material";
import PropTypes from "prop-types";

const DeleteConfirmationDialog = ({
  open,
  onClose,
  invitationId,
  setRefreshData,
  handleDelete,
  title,
  message,
}) => {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <DialogContentText>{message}</DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} color="primary">
          Cancel
        </Button>
        <Button
          onClick={() => handleDelete(invitationId, setRefreshData, onClose)}
          color="error"
        >
          Delete
        </Button>
      </DialogActions>
    </Dialog>
  );
};

DeleteConfirmationDialog.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  invitationId: PropTypes.bool,
  setRefreshData: PropTypes.string,
  handleDelete: PropTypes.func,
  title: PropTypes.string,
  message: PropTypes.string,
};

export default DeleteConfirmationDialog;
