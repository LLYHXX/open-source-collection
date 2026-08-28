import React from "react";
import { Helmet } from "react-helmet-async";
import TestRunsView from "src/sections/test/TestRuns/TestRunsView";

const TestRuns = () => {
  return (
    <>
      <Helmet>
        <title>Test Runs</title>
      </Helmet>
      <TestRunsView />
    </>
  );
};

export default TestRuns;
