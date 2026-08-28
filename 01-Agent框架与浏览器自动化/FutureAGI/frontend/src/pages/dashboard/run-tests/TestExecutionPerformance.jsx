import React from "react";
import { Helmet } from "react-helmet-async";
import PerformanceDetails from "src/sections/test-detail/PerformanceDetails";

const TestExecutionPerformance = () => {
  return (
    <>
      <Helmet>
        <title>Performance Details</title>
      </Helmet>
      <PerformanceDetails />
    </>
  );
};

export default TestExecutionPerformance;
