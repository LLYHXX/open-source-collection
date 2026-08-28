import { Box, useTheme } from "@mui/material";
import React, { useEffect } from "react";
import { ShowComponent } from "src/components/show";
import PropTypes from "prop-types";

import LoadingOutputSection from "../../LoadingSkeleton/LoadingOutputSection";
import useWavesurferCache from "src/hooks/use-wavesurfer-cache";

import PromptLoading from "./PromptLoading/PromptLoading";
import DefaultOutput from "./DefaultOutput";
import ResultSection from "./ResultSection";

const OutputSection = ({
  results,
  loadingPrompt,
  promptGeneratingStatus,
  selectedVersion,
  responseFormat,
  outputFormat,
}) => {
  const theme = useTheme();
  const {
    getWaveSurferInstance,
    storeWaveSurferInstance,
    updateWaveSurferInstance,
    clearWaveSurferCache,
  } = useWavesurferCache();

  useEffect(() => {
    return () => clearWaveSurferCache();
  }, [clearWaveSurferCache]);

  if (loadingPrompt) {
    return <LoadingOutputSection />;
  }

  return (
    <Box
      sx={{
        p: 2,
        // border: "1px solid",
        // borderColor: "divider",
        borderRadius: theme.spacing(1),
        height: "100%",
        overflow: "auto",
        bgcolor: "background.neutral",
      }}
    >
      <ShowComponent
        condition={Boolean(promptGeneratingStatus && !results?.output?.length)}
      >
        <PromptLoading />
      </ShowComponent>
      <ShowComponent
        condition={!results?.output?.length && !promptGeneratingStatus}
      >
        <DefaultOutput />
      </ShowComponent>
      <ShowComponent condition={Boolean(results?.output?.length)}>
        <ResultSection
          results={results}
          selectedVersion={selectedVersion}
          responseFormat={responseFormat}
          outputFormat={outputFormat}
          getWaveSurferInstance={getWaveSurferInstance}
          storeWaveSurferInstance={storeWaveSurferInstance}
          updateWaveSurferInstance={updateWaveSurferInstance}
        />
      </ShowComponent>
    </Box>
  );
};

OutputSection.propTypes = {
  results: PropTypes.object,
  loadingPrompt: PropTypes.bool,
  promptGeneratingStatus: PropTypes.bool,
  selectedVersion: PropTypes.object,
  responseFormat: PropTypes.object,
  outputFormat: PropTypes.string,
};

export default OutputSection;
