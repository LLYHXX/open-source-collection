import React from "react";
import { Helmet } from "react-helmet-async";
import AgentDetailsView from "src/sections/agents/AgentDetailsView";

const AgentDetails = () => {
  return (
    <>
      <Helmet>
        <title>Agent Definition Details</title>
      </Helmet>
      <AgentDetailsView />
    </>
  );
};

export default AgentDetails;
