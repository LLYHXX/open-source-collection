import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import EvalsOutput from "../../EvalDetails/EvalsConfig/EvalsOutput";

const RightOutputSection = ({ results }) => {
  return (
    <Box sx={{ flex: 1 }}>
      <EvalsOutput results={results} />
    </Box>
  );
};

export default RightOutputSection;
RightOutputSection.propTypes = {
  results: PropTypes.object,
};
