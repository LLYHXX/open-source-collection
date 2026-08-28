import { Box, Chip, Typography } from "@mui/material";
import React from "react";
import { alpha } from "@mui/material";

const FilterChipsRenderer = (params) => {
  const items = params.value || [];
  const firstItem = items[0];
  const remainingItems = items.length - 1;

  const chipStyles = {
    backgroundColor: (theme) => alpha(theme.palette.primary.main, 0.1),
    color: "primary.main",
    borderRadius: "4px",
    fontWeight: 500,
    fontSize: "12px",
    "&:hover": {
      backgroundColor: "action.hover",
      borderColor: "divider",
    },
  };

  if (!firstItem) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          height: "100%",
        }}
      >
        No Filters applied
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        height: "100%",
      }}
    >
      {firstItem && <Chip label={firstItem} size="small" sx={chipStyles} />}
      {remainingItems > 0 && (
        <Typography
          component="span"
          sx={{
            color: "text.primary",
            fontSize: "12px",
            pl: "10px",
          }}
        >
          +{remainingItems} other{remainingItems > 1 ? "s" : ""}
        </Typography>
      )}
    </Box>
  );
};

export default FilterChipsRenderer;
