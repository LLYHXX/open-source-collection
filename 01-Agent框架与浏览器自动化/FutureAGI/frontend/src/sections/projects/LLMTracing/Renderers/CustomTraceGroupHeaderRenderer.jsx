import { Box } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

const CustomTraceGroupHeaderRenderer = (props) => {
  return <Box>{props.displayName}</Box>;
};

CustomTraceGroupHeaderRenderer.propTypes = {
  displayName: PropTypes.string,
};

export default CustomTraceGroupHeaderRenderer;
