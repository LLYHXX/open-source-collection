import React from "react";
import PropTypes from "prop-types";
import { Typography } from "@mui/material";

export default function NumericCell({ value, sx }) {
  const numValue = Number(value);
  const safeValue = isNaN(numValue)
    ? "-"
    : Number.isInteger(numValue)
      ? String(numValue)
      : numValue.toFixed(4);
  return (
    <Typography
      typography="s3"
      color="text.primary"
      sx={{
        padding: 1,
        ...sx,
      }}
    >
      {safeValue}
    </Typography>
  );
}

NumericCell.propTypes = {
  value: PropTypes.number.isRequired,
  sx: PropTypes.object,
};
