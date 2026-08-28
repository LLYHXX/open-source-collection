import { Box, Divider, Drawer } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import CustomEvalsForm from "src/sections/common/EvaluationDrawer/CustomEvalsForm";

const CustomEvalsFormDrawer = ({ open, onClose, ...rest }) => {
  return (
    <Drawer
      anchor="right"
      open={open}
      variant="persistent"
      onClose={onClose}
      PaperProps={{
        sx: {
          height: "100vh",
          position: "fixed",
          zIndex: 2,
          boxShadow: "-10px 0px 100px #00000035",
          borderRadius: "0px !important",
          backgroundColor: "background.paper",
        },
      }}
      ModalProps={{
        BackdropProps: {
          style: {
            backgroundColor: "transparent",
            borderRadius: "0px !important",
          },
        },
      }}
    >
      <Box display="flex">
        <Divider orientation="vertical" />
        <Box sx={{ padding: "16px", overflow: "hidden" }}>
          <CustomEvalsForm onClose={onClose} showTest {...rest} />
        </Box>
      </Box>
    </Drawer>
  );
};

export default CustomEvalsFormDrawer;

CustomEvalsFormDrawer.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func,
};
