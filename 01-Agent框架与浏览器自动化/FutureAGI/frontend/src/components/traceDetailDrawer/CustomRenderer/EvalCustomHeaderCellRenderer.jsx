import { Box, Typography } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import Iconify from "src/components/iconify";

const EvalCustomHeaderCellRenderer = ({ displayName }) => {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 0.7,
        marginLeft: "-6px",
      }}
    >
      {displayName == "Score" ? (
        <Iconify
          width={16}
          icon="material-symbols:check-circle-outline"
          color="text.secondary"
        />
      ) : null}
      <Typography
        sx={{ fontSize: "13px", fontWeight: 700, color: "text.secondary" }}
      >
        {displayName}
      </Typography>
    </Box>
  );
};

EvalCustomHeaderCellRenderer.propTypes = {
  displayName: PropTypes.string,
};

export default EvalCustomHeaderCellRenderer;
