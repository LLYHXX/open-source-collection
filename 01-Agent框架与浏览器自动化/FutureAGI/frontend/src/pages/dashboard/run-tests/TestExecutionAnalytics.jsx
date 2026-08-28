import React from "react";
import { Helmet } from "react-helmet-async";
import AnalyticsDetails from "src/sections/test-detail/AnalyticsDetails";

const TestExecutionAnalytics = () => {
  return (
    <>
      <Helmet>
        <title>Analytics Details</title>
      </Helmet>
      <AnalyticsDetails />
    </>
  );
};

export default TestExecutionAnalytics;
