import React, { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  Button,
  CircularProgress,
  Box,
  Alert,
} from "@mui/material";
import PropTypes from "prop-types";
import axios, { endpoints } from "src/utils/axios";

const DeleteScenarioDialog = ({ open, onClose, scenario, onDeleteSuccess }) => {
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState("");

  const handleClose = () => {
    if (!isDeleting) {
      setError("");
      onClose();
    }
  };

  const handleDelete = async () => {
    if (!scenario?.id) return;

    setIsDeleting(true);
    setError("");

    try {
      await axios.delete(endpoints.scenarios.delete(scenario.id));
      onDeleteSuccess?.();
      handleClose();
    } catch (err) {
      // console.error("Error deleting scenario:", err);
      setError(
        err.response?.data?.error ||
          err.message ||
          "Failed to delete scenario. Please try again.",
      );
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: {
          width: "400px",
        },
      }}
    >
      <DialogTitle>
        <Typography variant="h6" fontWeight="fontWeightSemiBold">
          Delete Scenario
        </Typography>
      </DialogTitle>

      <DialogContent>
        <Box sx={{ pt: 1 }}>
          <Typography variant="body1" color="text.primary" gutterBottom>
            Are you sure you want to delete this scenario?
          </Typography>

          <Box
            sx={{
              backgroundColor: "background.default",
              p: 2,
              borderRadius: 1,
              mt: 2,
              border: "1px solid",
              borderColor: "divider",
            }}
          >
            <Typography variant="subtitle2" fontWeight="fontWeightSemiBold">
              {scenario?.name}
            </Typography>
            {scenario?.description && (
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 0.5 }}
              >
                {scenario.description}
              </Typography>
            )}
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            This action cannot be undone. The scenario and its associated data
            will be permanently removed.
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {error}
            </Alert>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 3, pt: 1 }}>
        <Button onClick={handleClose} color="inherit" disabled={isDeleting}>
          Cancel
        </Button>
        <Button
          onClick={handleDelete}
          variant="contained"
          color="error"
          disabled={isDeleting}
          startIcon={
            isDeleting ? <CircularProgress size={16} color="inherit" /> : null
          }
        >
          {isDeleting ? "Deleting..." : "Delete Scenario"}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

DeleteScenarioDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  scenario: PropTypes.object,
  onDeleteSuccess: PropTypes.func,
};

export default DeleteScenarioDialog;
