import React from "react";
import { Helmet } from "react-helmet-async";
import { AudioPlaybackProvider } from "src/components/custom-audio/context-provider/AudioPlaybackContext";
import IndividualExperimentWrapperView from "src/sections/experiment-detail/IndividualExperimentWrapperView";

const IndividualExperimentWrapper = () => {
  return (
    <>
      <Helmet>
        <title>Individual Experiment</title>
      </Helmet>
      <AudioPlaybackProvider>
        <IndividualExperimentWrapperView />
      </AudioPlaybackProvider>
    </>
  );
};

export default IndividualExperimentWrapper;
