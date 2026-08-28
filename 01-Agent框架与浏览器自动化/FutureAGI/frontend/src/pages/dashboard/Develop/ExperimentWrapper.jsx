import React from "react";
import { Helmet } from "react-helmet-async";
import ExperimentWrapperView from "src/sections/experiment-detail/ExperimentWrapperView";

const ExperimentWrapper = () => {
  return (
    <>
      <Helmet>
        <title>Experiment</title>
      </Helmet>
      <ExperimentWrapperView />
    </>
  );
};

export default ExperimentWrapper;
