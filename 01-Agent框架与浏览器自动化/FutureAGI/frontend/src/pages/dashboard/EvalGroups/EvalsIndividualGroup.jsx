import React from "react";
import EvalsWrapper from "src/sections/evals/EvalsWrapper";
import IndividualGroup from "src/sections/evals/Groups/IndividualGroup";

const EvalsIndividualGroup = () => {
  return (
    <EvalsWrapper currentTab="groups">
      <IndividualGroup />
    </EvalsWrapper>
  );
};

export default EvalsIndividualGroup;
