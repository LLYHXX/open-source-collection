import React from "react";
import { Helmet } from "react-helmet-async";
import FallbacksSection from "src/sections/gateway/fallbacks/FallbacksSection";

const GatewayFallbacks = () => (
  <>
    <Helmet>
      <title>Gateway Fallbacks | Future AGI</title>
    </Helmet>
    <FallbacksSection />
  </>
);

export default GatewayFallbacks;
