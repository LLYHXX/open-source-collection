import { Box, Typography } from "@mui/material";
import React from "react";

import EvaluationActions from "./EvaluationActions";
import EvaluationData from "./EvaluationData/EvaluationData";
import WorkbenchEvaluationProvider from "./context/WorkbenchEvaluationProvider";

const Evaluation = () => {
  return (
    <WorkbenchEvaluationProvider>
      <Box
        display="flex"
        flexDirection={"column"}
        width="100%"
        height="100%"
        gap={0.5}
        paddingX={2}
        sx={{
          overflow: "hidden",
        }}
      >
        <EvaluationActions />
        <Typography typography={"s2"}>
          NA : Yet to run Evals for this cell. Will be updated once run prompt
          and evaluate run is completed
        </Typography>
        <EvaluationData />
      </Box>
    </WorkbenchEvaluationProvider>
  );
};

export default Evaluation;
