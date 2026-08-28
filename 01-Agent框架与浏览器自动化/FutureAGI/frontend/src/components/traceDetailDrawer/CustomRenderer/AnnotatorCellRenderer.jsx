import React from "react";
import PropTypes from "prop-types";
import { Avatar, Box } from "@mui/material";

const AnnotatorCellRenderer = (props) => {
  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, height: "100%" }}>
      <Avatar sx={{ width: 24, height: 24 }} />
      {props.value}
    </Box>
  );
};

AnnotatorCellRenderer.propTypes = {
  value: PropTypes.string,
};

export default AnnotatorCellRenderer;
