import { Box, Typography } from "@mui/material";
import React from "react";
import Iconify from "src/components/iconify";
import PropTypes from "prop-types";

const WizardInputHelpText = ({ text }) => {
  return (
    <Box sx={{ display: "flex", gap: 0.5, alignItems: "center" }}>
      <Iconify icon="solar:info-circle-bold" color="text.disabled" />
      <Typography variant="caption" color="text.secondary">
        {text}
      </Typography>
    </Box>
  );
};

WizardInputHelpText.propTypes = {
  text: PropTypes.string,
};

export default WizardInputHelpText;
