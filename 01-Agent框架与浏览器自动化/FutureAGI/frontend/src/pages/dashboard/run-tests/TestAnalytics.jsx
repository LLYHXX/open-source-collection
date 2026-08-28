import React from "react";
import { Helmet } from "react-helmet-async";
import TestAnalyticsView from "src/sections/test/Analytics/TestAnalyticsView";

const TestAnalytics = () => {
  return (
    <>
      <Helmet>
        <title>Analytics</title>
      </Helmet>
      <TestAnalyticsView />
    </>
  );
};

export default TestAnalytics;
