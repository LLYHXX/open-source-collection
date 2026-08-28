import React from "react";
import { Helmet } from "react-helmet-async";
import ExperimentSummaryView from "src/sections/experiment-detail/ExperimentSummary/ExperimentSummaryView";

const ExperimentSummary = () => {
  return (
    <>
      <Helmet>
        <title>Experiment Summary</title>
      </Helmet>
      <ExperimentSummaryView />
    </>
  );
};

export default ExperimentSummary;
