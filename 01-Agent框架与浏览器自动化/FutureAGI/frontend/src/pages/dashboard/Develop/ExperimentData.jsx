import React from "react";
import { Helmet } from "react-helmet-async";
import { AudioPlaybackProvider } from "src/components/custom-audio/context-provider/AudioPlaybackContext";
import ExperimentDataView from "src/sections/experiment-detail/ExperimentData/ExperimentDataView";

const ExperimentData = () => {
  return (
    <>
      <Helmet>
        <title>Experiment Data</title>
      </Helmet>
      <AudioPlaybackProvider>
        <ExperimentDataView />
      </AudioPlaybackProvider>
    </>
  );
};

export default ExperimentData;
