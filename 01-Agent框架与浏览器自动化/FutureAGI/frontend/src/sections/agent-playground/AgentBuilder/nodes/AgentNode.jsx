import React, { memo } from "react";
import PropTypes from "prop-types";
import BaseNode from "./BaseNode";
import { NODE_TYPES } from "../../utils/constants";

const AgentNode = ({ id, data, isConnectable, selected }) => {
  return (
    <BaseNode
      id={id}
      data={data}
      isConnectable={isConnectable}
      selected={selected}
      type={NODE_TYPES.AGENT}
    />
  );
};

AgentNode.propTypes = {
  id: PropTypes.string.isRequired,
  data: PropTypes.object.isRequired,
  isConnectable: PropTypes.bool,
  selected: PropTypes.bool,
};

export default memo(AgentNode);
