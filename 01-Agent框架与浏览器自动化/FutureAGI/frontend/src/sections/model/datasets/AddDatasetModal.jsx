import React from "react";
import { ModalComponent } from "src/components/ModalComponent";
import PropTypes from "prop-types";
import { Box, Button, Typography } from "@mui/material";

const AddDatasetModal = ({ open, onClose }) => {
  return (
    <ModalComponent open={open} onClose={onClose}>
      <Box
        sx={{ padding: 2, display: "flex", flexDirection: "column", gap: 2 }}
      >
        <Typography variant="h5">Add Dataset</Typography>
        <Box>Some documentation here </Box>
        <Box sx={{ display: "flex", justifyContent: "flex-end" }}>
          <Button onClick={() => onClose()}>Close</Button>
        </Box>
      </Box>
    </ModalComponent>
  );
};

AddDatasetModal.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
};

export default AddDatasetModal;
