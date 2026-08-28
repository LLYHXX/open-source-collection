import React from "react";
import { Box, Typography, LinearProgress, styled } from "@mui/material";
import PropTypes from "prop-types";
import { typography } from "src/theme/typography";

const Label = styled(Typography)(({ theme }) => ({
  color: theme.palette.text.secondary,
  fontFamily: typography.fontFamily,
  ...typography.caption,
}));

const Progressbar = ({ value, data }) => {
  const reverseOutput = data?.reverseOutput;

  const formattedValue = reverseOutput
    ? 100 - parseFloat(value)
    : parseFloat(value);

  return (
    <Box display="flex" alignItems="center" gap={1}>
      <LinearProgress
        variant="determinate"
        value={formattedValue}
        sx={{ width: "341px", height: "4px", borderRadius: "4px", flex: 1 }}
        color="success"
      />
      <Label>{formattedValue}%</Label>
    </Box>
  );
};

Progressbar.propTypes = {
  value: PropTypes.string,
  data: PropTypes.object,
};

export default Progressbar;
