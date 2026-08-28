import React, { useMemo } from "react";
import PropTypes from "prop-types";

import { usePromptWorkbenchContext } from "../../WorkbenchContext";
import SingleImageViewerProvider from "src/sections/develop-detail/Common/SingleImageViewer/SingleImageViewerProvider";

import SingleResult from "./SingleResult";
import MultiResult from "./MultiResult";

const ResultSection = ({
  results,
  selectedVersion,
  responseFormat,
  outputFormat,
  getWaveSurferInstance,
  storeWaveSurferInstance,
  updateWaveSurferInstance,
}) => {
  const { variableData } = usePromptWorkbenchContext();

  const datapointCount = useMemo(() => {
    return Object.values(variableData || {}).reduce((acc, value) => {
      // value is an array find total non empty strings
      const eachValues = value.filter((v) => v !== "").length;
      if (eachValues > acc) {
        acc = eachValues;
      }
      return acc;
    }, 0);
  }, [variableData]);

  if (datapointCount <= 1) {
    return (
      <SingleImageViewerProvider>
        <SingleResult
          result={results?.output?.[0]}
          isAnimating={results?.isAnimating}
          selectedVersion={selectedVersion}
          responseFormat={responseFormat}
          outputFormat={outputFormat}
          getWaveSurferInstance={getWaveSurferInstance}
          storeWaveSurferInstance={storeWaveSurferInstance}
          updateWaveSurferInstance={updateWaveSurferInstance}
        />
      </SingleImageViewerProvider>
    );
  }
  return (
    <SingleImageViewerProvider>
      <MultiResult
        results={results?.output}
        selectedVersion={selectedVersion}
        responseFormat={responseFormat}
        outputFormat={outputFormat}
        getWaveSurferInstance={getWaveSurferInstance}
        storeWaveSurferInstance={storeWaveSurferInstance}
        updateWaveSurferInstance={updateWaveSurferInstance}
      />
    </SingleImageViewerProvider>
  );
};

ResultSection.propTypes = {
  results: PropTypes.any,
  selectedVersion: PropTypes.object,
  responseFormat: PropTypes.object,
  outputFormat: PropTypes.string,
  getWaveSurferInstance: PropTypes.func,
  storeWaveSurferInstance: PropTypes.func,
  updateWaveSurferInstance: PropTypes.func,
};

export default ResultSection;
