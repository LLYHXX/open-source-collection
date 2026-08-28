import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const OptimizeRunningModel = ({ open, onClose }) => {
  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Optimization is running ...</DialogTitle>
      <DialogContent>
        <Typography variant="body2">
          Optimization is still running, it should take about an hour to
          complete depending on size of dataset.
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} variant="contained" color="primary">
          Okay
        </Button>
      </DialogActions>
    </Dialog>
  );
};

OptimizeRunningModel.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
};

export default OptimizeRunningModel;
