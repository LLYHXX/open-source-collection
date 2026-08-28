import React, { memo } from "react";
import PropTypes from "prop-types";
import BaseNode from "./BaseNode";

const EvalNode = ({ id, data, isConnectable, selected }) => {
  return (
    <BaseNode
      id={id}
      data={data}
      isConnectable={isConnectable}
      selected={selected}
    />
  );
};

EvalNode.propTypes = {
  id: PropTypes.string.isRequired,
  data: PropTypes.object.isRequired,
  isConnectable: PropTypes.bool,
  selected: PropTypes.bool,
};

export default memo(EvalNode);
