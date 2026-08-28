import { Box } from "@mui/material";
import React from "react";

import { usePromptWorkbenchContext } from "../WorkbenchContext";
import OutputSection from "../Playground/OutputSection/OutputSection";

const CompareOutputs = () => {
  const {
    promptGeneratingStatus,
    results,
    loadingPrompt,
    selectedVersions,
    modelConfig,
  } = usePromptWorkbenchContext();

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        gap: 2,
        overflow: "hidden",
        height: "100%",
      }}
    >
      {selectedVersions.map(({ id }, index) => (
        <Box
          key={id}
          sx={{
            flex: 1,
            borderRightStyle: "solid",
            borderRightColor: "divider",
            borderRightWidth:
              index < selectedVersions.length - 1 ? "1px" : "0px",
            paddingRight: index < selectedVersions.length - 1 ? 2 : 0,
            paddingTop: 2,
            overflowY: "hidden",
            height: "100%",
          }}
        >
          <OutputSection
            results={results[index]}
            loadingPrompt={loadingPrompt}
            promptGeneratingStatus={promptGeneratingStatus[index]}
            selectedVersion={selectedVersions[index]}
            responseFormat={modelConfig?.[index]?.responseFormat}
            outputFormat={modelConfig?.[index]?.output_format}
          />
        </Box>
      ))}
    </Box>
  );
};

export default CompareOutputs;
