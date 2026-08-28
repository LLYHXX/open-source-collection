import React from "react";
import { Helmet } from "react-helmet-async";
import CreateNewAgentDefinitionView from "src/sections/agents/CreateNewAgentDefinitionView";

const CreateNewAgentDefinition = () => {
  return (
    <>
      <Helmet>
        <title>Agent Definition Details</title>
      </Helmet>
      <CreateNewAgentDefinitionView />
    </>
  );
};

export default CreateNewAgentDefinition;
