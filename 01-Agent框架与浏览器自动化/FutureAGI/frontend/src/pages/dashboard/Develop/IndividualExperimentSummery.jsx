import React from "react";
import { Helmet } from "react-helmet-async";
import IndividualExperimentSummaryView from "src/sections/experiment-detail/ExperimentSummary/IndividualExperimentSummaryView";

const IndividualExperimentSummary = () => {
  return (
    <>
      <Helmet>
        <title>Individual Experiment Summary</title>
      </Helmet>
      <IndividualExperimentSummaryView />
    </>
  );
};

export default IndividualExperimentSummary;
