import React from "react";
import { Helmet } from "react-helmet-async";
import EvalsUsageView from "src/sections/evals/EvalsUsageView";

const EvalsUsage = () => {
  return (
    <>
      <Helmet>
        <title>Evaluations Usage</title>
      </Helmet>
      <EvalsUsageView />
    </>
  );
};

export default EvalsUsage;
