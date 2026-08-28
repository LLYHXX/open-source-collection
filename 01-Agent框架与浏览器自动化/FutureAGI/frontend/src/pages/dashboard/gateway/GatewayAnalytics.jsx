import React from "react";
import { Helmet } from "react-helmet-async";
import AnalyticsDashboardSection from "src/sections/gateway/analytics/AnalyticsDashboardSection";

const GatewayAnalytics = () => {
  return (
    <>
      <Helmet>
        <title>Analytics | Gateway</title>
      </Helmet>
      <AnalyticsDashboardSection />
    </>
  );
};

export default GatewayAnalytics;
