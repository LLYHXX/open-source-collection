import React from "react";
import { Helmet } from "react-helmet-async";
import CreateScenarioView from "src/sections/scenarios/CreateScenarioView";

const CreateScenario = () => {
  return (
    <>
      <Helmet>
        <title>Create Scenario</title>
      </Helmet>
      <CreateScenarioView />
    </>
  );
};

export default CreateScenario;
