import { Box, useTheme } from "@mui/material";
import React from "react";
import { ShowComponent } from "src/components/show";
import { usePromptWorkbenchContext } from "./WorkbenchContext";
import Evaluation from "./Evaluation";
import Playground from "./Playground";
import PromptActions from "./promptActions/PromptActions";
import Metrics from "./Metrics/Metrics";
import Simulate from "./Simulate";

const PromptContainer = () => {
  const theme = useTheme();
  const { currentTab } = usePromptWorkbenchContext();

  return (
    <Box
      display="flex"
      flexDirection={"column"}
      justifyContent={"space-between"}
      gap={theme.spacing(1)}
      width="100%"
      height="100%"
      sx={{
        overflow: "hidden",
      }}
    >
      <PromptActions />
      <ShowComponent condition={currentTab === "Playground"}>
        <Playground />
      </ShowComponent>
      <ShowComponent condition={currentTab === "Evaluation"}>
        <Evaluation />
      </ShowComponent>
      <ShowComponent condition={currentTab === "Metrics"}>
        <Metrics />
      </ShowComponent>
      <ShowComponent condition={currentTab === "Simulation"}>
        <Simulate />
      </ShowComponent>
    </Box>
  );
};

export default PromptContainer;
