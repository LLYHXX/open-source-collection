import React from "react";
import { Helmet } from "react-helmet-async";
import IndividualExperimentDataView from "src/sections/experiment-detail/ExperimentData/IndividualExperimentDataView";

const IndividualExperimentData = () => {
  return (
    <>
      <Helmet>
        <title>Individual Experiment Data</title>
      </Helmet>
      <IndividualExperimentDataView />
    </>
  );
};

export default IndividualExperimentData;
