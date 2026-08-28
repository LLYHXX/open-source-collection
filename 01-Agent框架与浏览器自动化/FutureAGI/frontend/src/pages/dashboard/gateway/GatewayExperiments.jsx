import React from "react";
import { Helmet } from "react-helmet-async";
import ExperimentsSection from "src/sections/gateway/experiments/ExperimentsSection";

const GatewayExperiments = () => (
  <>
    <Helmet>
      <title>Shadow Experiments | Gateway</title>
    </Helmet>
    <ExperimentsSection />
  </>
);

export default GatewayExperiments;
