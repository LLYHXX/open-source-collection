import React from "react";
import { Helmet } from "react-helmet-async";
import AlertingMonitoringSection from "src/sections/gateway/monitoring/AlertingMonitoringSection";

const GatewayMonitoring = () => (
  <>
    <Helmet>
      <title>Gateway Monitoring | Future AGI</title>
    </Helmet>
    <AlertingMonitoringSection />
  </>
);

export default GatewayMonitoring;
