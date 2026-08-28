import { Box, Stack } from "@mui/material";
import React, { useState } from "react";
import LeftInputSection from "./LeftInputSection";
import RightOutputSection from "./RightOutputSection";
import PropTypes from "prop-types";

const TopEvaluateSection = ({ evaluation, refreshGrid, setSelectedData }) => {
  const [results, setResults] = useState(null);
  return (
    <Stack sx={{ paddingBottom: "14px", height: "100%" }} direction="row">
      <LeftInputSection
        evaluation={evaluation}
        setResults={setResults}
        refreshGrid={refreshGrid}
        setSelectedData={setSelectedData}
      />
      <Box
        sx={{
          width: "1px",
          height: "100%",
          backgroundColor: "background.paper",
          marginX: 2,
        }}
      />
      <RightOutputSection results={results} />
    </Stack>
  );
};

TopEvaluateSection.propTypes = {
  evaluation: PropTypes.object,
  refreshGrid: PropTypes.func,
  setSelectedData: PropTypes.func,
};

export default TopEvaluateSection;
