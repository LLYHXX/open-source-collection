import React, { memo } from "react";
import PropTypes from "prop-types";
import BaseNode from "./BaseNode";
import { NODE_TYPES } from "../../utils/constants";

const PromptNode = ({ id, data, isConnectable, selected }) => {
  return (
    <BaseNode
      id={id}
      data={data}
      isConnectable={isConnectable}
      selected={selected}
      type={NODE_TYPES.LLM_PROMPT}
    />
  );
};

PromptNode.propTypes = {
  id: PropTypes.string.isRequired,
  data: PropTypes.object.isRequired,
  isConnectable: PropTypes.bool,
  selected: PropTypes.bool,
};

export default memo(PromptNode);
