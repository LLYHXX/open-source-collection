import React, { createContext, useState } from "react";
import PropTypes from "prop-types"; // Import PropTypes

const SelectedNodeContext = createContext({
  selectedNode: null,
  setSelectedNode: (_value) => {},
});

export const SelectedNodeProvider = ({ children }) => {
  const [selectedNode, setSelectedNode] = useState(null);

  const value = {
    selectedNode,
    setSelectedNode,
  };

  return (
    <SelectedNodeContext.Provider value={value}>
      {children}
    </SelectedNodeContext.Provider>
  );
};

// Add prop-types validation for `children`
SelectedNodeProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

export default SelectedNodeContext;
