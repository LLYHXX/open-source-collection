import React from "react";
import PropTypes from "prop-types";
import { TextField } from "@mui/material";

const ConfigureEndCallNode = ({ node, onChange }) => {
  return (
    <>
      <TextField
        label="Prompt"
        value={node?.data?.prompt || ""}
        onChange={(e) => {
          onChange(node?.id, (existingNode) => ({
            ...existingNode,
            data: {
              ...existingNode.data,
              prompt: e.target.value,
            },
          }));
        }}
        size="small"
        multiline
        rows={4}
        fullWidth
        placeholder="Enter prompt for conversation"
      />
    </>
  );
};

ConfigureEndCallNode.propTypes = {
  node: PropTypes.object,
  onChange: PropTypes.func,
};

export default ConfigureEndCallNode;
