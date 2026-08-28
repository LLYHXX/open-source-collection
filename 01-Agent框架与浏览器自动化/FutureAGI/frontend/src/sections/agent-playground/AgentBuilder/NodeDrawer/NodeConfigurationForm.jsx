import React from "react";
import PropTypes from "prop-types";
import { PromptNodeForm, EvalsNodeForm, AgentNodeForm } from "./forms";
import { NODE_TYPES } from "../../utils/constants";

const FORM_COMPONENTS = {
  [NODE_TYPES.LLM_PROMPT]: PromptNodeForm,
  eval: EvalsNodeForm,
  [NODE_TYPES.AGENT]: AgentNodeForm,
};

export default function NodeConfigurationForm({ nodeType, nodeId }) {
  const FormComponent = FORM_COMPONENTS[nodeType];

  if (!FormComponent) {
    return null;
  }

  return <FormComponent nodeId={nodeId} />;
}

NodeConfigurationForm.propTypes = {
  nodeType: PropTypes.oneOf([NODE_TYPES.LLM_PROMPT, "eval", NODE_TYPES.AGENT])
    .isRequired,
  nodeId: PropTypes.string.isRequired,
};
