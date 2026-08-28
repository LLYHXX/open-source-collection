import React from "react";
import { Helmet } from "react-helmet-async";
import PromptView from "src/sections/prompt/PromptView";

const Prompt = () => {
  return (
    <>
      <Helmet>
        <title>Prompts</title>
      </Helmet>
      <PromptView />
    </>
  );
};

export default Prompt;
