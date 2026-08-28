import React from "react";
import { Helmet } from "react-helmet-async";
import RequestExplorerSection from "src/sections/gateway/logs/RequestExplorerSection";

const GatewayLogs = () => {
  return (
    <>
      <Helmet>
        <title>Request Logs | Gateway</title>
      </Helmet>
      <RequestExplorerSection />
    </>
  );
};

export default GatewayLogs;
