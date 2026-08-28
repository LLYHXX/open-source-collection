import React from "react";
import { Helmet } from "react-helmet-async";
import ExperimentListView from "src/sections/project/ExperimentListView";

const ProjectList = () => {
  return (
    <>
      <Helmet>
        <title>Project - Experiment</title>
      </Helmet>
      <ExperimentListView />
    </>
  );
};

export default ProjectList;
