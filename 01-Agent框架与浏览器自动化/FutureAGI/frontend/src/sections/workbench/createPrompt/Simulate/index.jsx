import { Box } from "@mui/material";
import React from "react";

import SimulateActions from "./SimulateActions";
import SimulateContent from "./SimulateContent/SimulateContent";

const Simulate = () => {
  return (
    <Box
      display="flex"
      flexDirection={"column"}
      width="100%"
      height="100%"
      gap={1}
      paddingX={2}
      sx={{
        overflow: "hidden",
      }}
    >
      <SimulateActions />
      <SimulateContent />
    </Box>
  );
};

export default Simulate;
