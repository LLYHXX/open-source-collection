import { Icon } from "@iconify/react";
import { LoadingButton } from "@mui/lab";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogTitle,
  IconButton,
  Typography,
} from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const DeleteEvalConfirm = ({
  open,
  onClose,
  onConfirm,
  onConfirmWithColumn,
  isLoading,
}) => {
  return (
    <Dialog
      open={open}
      onClose={onClose}
      aria-labelledby="confirm-dialog-title"
      aria-describedby="confirm-dialog-description"
      PaperProps={{
        sx: {
          minWidth: "581px",
        },
      }}
    >
      <DialogTitle
        sx={{
          gap: "10px",
          display: "flex",
          flexDirection: "column",
          padding: 2,
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Typography fontSize={16} fontWeight={700} color={"text.primary"}>
            Are you sure you want delete this evaluation
          </Typography>
          <IconButton onClick={onClose} sx={{ p: 0, color: "text.primary" }}>
            <Icon icon="mingcute:close-line" />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogActions sx={{ paddingY: 2 }}>
        <Button
          onClick={onClose}
          variant="outlined"
          sx={{
            fontSize: "12px",
            fontWeight: 500,
            paddingX: "24px",
            paddingY: "6px",
          }}
        >
          Cancel
        </Button>

        <LoadingButton
          loading={isLoading}
          onClick={onConfirm}
          variant="outlined"
          autoFocus
          color="error"
          sx={{
            fontSize: "12px",
            fontWeight: 500,
            paddingX: "24px",
            paddingY: "6px",
            border: "1px solid",
            borderColor: "error.main",
            "&:hover": {
              borderColor: "error.main",
              backgroundColor: "red.o10",
            },
          }}
        >
          Delete Evaluation only
        </LoadingButton>
        <LoadingButton
          loading={isLoading}
          onClick={onConfirmWithColumn}
          variant="contained"
          autoFocus
          color="error"
          sx={{
            fontSize: "12px",
            fontWeight: 500,
            paddingX: "24px",
            paddingY: "6px",
          }}
        >
          Remove evaluation and result
        </LoadingButton>
      </DialogActions>
    </Dialog>
  );
};

DeleteEvalConfirm.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  onConfirm: PropTypes.func,
  onConfirmWithColumn: PropTypes.func,
  isLoading: PropTypes.bool,
};

export default DeleteEvalConfirm;
