import React from "react";
import { Helmet } from "react-helmet-async";
import GatewayOverviewSection from "src/sections/gateway/GatewayOverviewSection";

const GatewayOverview = () => {
  return (
    <>
      <Helmet>
        <title>Gateway</title>
      </Helmet>
      <GatewayOverviewSection />
    </>
  );
};

export default GatewayOverview;
