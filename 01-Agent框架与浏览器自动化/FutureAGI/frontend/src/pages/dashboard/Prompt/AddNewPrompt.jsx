import React from "react";
import { Helmet } from "react-helmet-async";
import AddNewPromptView from "src/sections/prompt/NewPrompt/AddNewPrompt";

const AddNewPrompt = () => {
  return (
    <>
      <Helmet>
        <title>Prompts</title>
      </Helmet>
      <AddNewPromptView />
    </>
  );
};

export default AddNewPrompt;
