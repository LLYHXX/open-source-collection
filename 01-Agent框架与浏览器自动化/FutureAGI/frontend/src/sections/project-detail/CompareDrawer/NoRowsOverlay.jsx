import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";

const NoRowsOverlay = (title) => {
  return (
    <Box
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%",
        color: "text.primary",
        fontWeight: "400",
        fontSize: "14px",
        lineHeight: "22px",
      }}
    >
      {title}
    </Box>
  );
};

NoRowsOverlay.propTypes = {
  title: PropTypes.string || PropTypes.node,
};

export default NoRowsOverlay;
