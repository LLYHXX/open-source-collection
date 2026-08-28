import {
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Typography,
} from "@mui/material";
import React from "react";
import Iconify from "src/components/iconify";
import CreateEditOptimizationForm from "./CreateEditOptimizationForm";
import PropTypes from "prop-types";
import SvgColor from "src/components/svg-color";

const RerunOptimizationModal = ({
  open,
  onClose,
  defaultValues,
  onSuccess,
}) => {
  return (
    <Dialog open={open} onClose={onClose} width="480px" fullWidth>
      <DialogTitle
        sx={{
          padding: 2,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Typography typography="m2" fontWeight="fontWeightMedium">
          Rerun Optimization
        </Typography>
        <IconButton
          onClick={onClose}
          size="small"
          sx={{
            color: "text.primary",
          }}
        >
          <Iconify icon="akar-icons:cross" />
        </IconButton>
      </DialogTitle>
      <DialogContent sx={{ padding: 2 }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            backgroundColor: "blue.o5",
            paddingX: "12px",
            paddingY: "4px",
            borderRadius: "4px",
            marginBottom: 2,
          }}
        >
          <SvgColor
            src="/assets/icons/ic_info.svg"
            sx={{ width: 16, height: 16, color: "blue.500" }}
          />
          <Typography typography="s2">
            Rerunning this optimization will create a new run
          </Typography>
        </Box>
        <Box sx={{ paddingTop: 0.5 }}>
          <CreateEditOptimizationForm
            onClose={onClose}
            defaultValues={defaultValues}
            onSuccess={onSuccess}
          />
        </Box>
      </DialogContent>
    </Dialog>
  );
};

RerunOptimizationModal.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
  defaultValues: PropTypes.object,
  onSuccess: PropTypes.func,
};

export default RerunOptimizationModal;
