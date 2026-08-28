/* eslint-disable react/prop-types */
import React from "react";
import { Chip } from "@mui/material";

const InheritedBadge = ({ variant = "inherited" }) => {
  if (variant === "custom") {
    return (
      <Chip
        label="Custom"
        size="small"
        variant="outlined"
        color="primary"
        sx={{ fontSize: "0.7rem", height: 22 }}
      />
    );
  }

  return (
    <Chip
      label="Inherited"
      size="small"
      variant="outlined"
      sx={{
        fontSize: "0.7rem",
        height: 22,
        color: "text.secondary",
        borderColor: "divider",
      }}
    />
  );
};

export default InheritedBadge;
